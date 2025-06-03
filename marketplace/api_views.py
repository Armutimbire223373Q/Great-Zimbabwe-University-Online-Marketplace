from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Listing, Category, Cart, CartItem, Purchase, Review, ListingImage
from .serializers import (
    ListingSerializer, CategorySerializer, CartSerializer,
    CartItemSerializer, PurchaseSerializer, ReviewSerializer
)
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Category.objects.all()
        if self.action == 'list':
            queryset = queryset.filter(parent_category=None)
        return queryset

    @action(detail=True, methods=['get'])
    def subcategories(self, request, slug=None):
        category = self.get_object()
        subcategories = Category.objects.filter(parent_category=category)
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Listing.objects.filter(status='active')
        category = self.request.query_params.get('category', None)
        search = self.request.query_params.get('search', None)
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        condition = self.request.query_params.get('condition', None)

        if category:
            queryset = queryset.filter(category__slug=category)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if condition:
            queryset = queryset.filter(condition=condition)

        return queryset

    def perform_create(self, serializer):
        images = self.request.FILES.getlist('images')
        if not images and serializer.validated_data.get('status') == 'active':
            raise serializers.ValidationError('Active listings must have at least one image.')
        
        listing = serializer.save(owner=self.request.user)
        
        for image in images:
            ListingImage.objects.create(listing=listing, image=image)

    def perform_update(self, serializer):
        images = self.request.FILES.getlist('images')
        if not images and serializer.validated_data.get('status') == 'active':
            raise serializers.ValidationError('Active listings must have at least one image.')
        
        listing = serializer.save()
        
        # Delete existing images if new ones are provided
        if images:
            listing.images.all().delete()
            for image in images:
                ListingImage.objects.create(listing=listing, image=image)

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=True, methods=['post'])
    def add_to_cart(self, request, pk=None):
        listing = self.get_object()
        quantity = int(request.data.get('quantity', 1))
        
        if listing.owner == request.user:
            return Response(
                {'error': 'You cannot add your own listings to cart.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if quantity > listing.quantity:
            return Response(
                {'error': 'Quantity exceeds available stock.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            listing=listing,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_object(self):
        return get_object_or_404(Cart, user=self.request.user)

    @action(detail=True, methods=['post'])
    def update_item(self, request, pk=None):
        cart = self.get_object()
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            cart_item = cart.items.get(id=item_id)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if quantity <= 0:
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if quantity > cart_item.listing.quantity:
            return Response(
                {'error': 'Quantity exceeds available stock.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        cart = self.get_object()
        item_id = request.data.get('item_id')

        try:
            cart_item = cart.items.get(id=item_id)
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        cart = self.get_object()
        if not cart.items.exists():
            return Response(
                {'error': 'Cart is empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create purchases for each item
        purchases = []
        for item in cart.items.all():
            purchase = Purchase.objects.create(
                listing=item.listing,
                buyer=request.user,
                seller=item.listing.owner,
                price=item.listing.price * item.quantity,
                meetup_location=request.data.get('meetup_location'),
                meetup_time=request.data.get('meetup_time'),
                message=request.data.get('message', '')
            )
            purchases.append(purchase)

        # Clear the cart
        cart.items.all().delete()

        serializer = PurchaseSerializer(purchases, many=True)
        return Response(serializer.data)

class PurchaseViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Purchase.objects.filter(
            Q(buyer=self.request.user) | Q(seller=self.request.user)
        )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        purchase = self.get_object()
        new_status = request.data.get('status')
        
        if purchase.seller != request.user:
            return Response(
                {'error': 'Only the seller can update the status.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if new_status not in dict(Purchase.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        purchase.status = new_status
        purchase.save()

        serializer = self.get_serializer(purchase)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_payment_status(self, request, pk=None):
        purchase = self.get_object()
        new_status = request.data.get('payment_status')
        
        if purchase.buyer != request.user:
            return Response(
                {'error': 'Only the buyer can update the payment status.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if new_status not in dict(Purchase.PAYMENT_STATUS_CHOICES):
            return Response(
                {'error': 'Invalid payment status.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        purchase.payment_status = new_status
        purchase.save()

        serializer = self.get_serializer(purchase)
        return Response(serializer.data)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Review.objects.filter(reviewed=self.request.user)

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        review = self.get_object()
        if request.user == review.reviewer:
            return Response(
                {'error': 'You cannot mark your own review as helpful.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        review.helpful_count += 1
        review.save()

        serializer = self.get_serializer(review)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        review = self.get_object()
        if request.user != review.reviewed:
            return Response(
                {'error': 'Only the reviewed user can respond.'},
                status=status.HTTP_403_FORBIDDEN
            )

        response = request.data.get('response')
        if not response:
            return Response(
                {'error': 'Response is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        review.response = response
        review.save()

        serializer = self.get_serializer(review)
        return Response(serializer.data) 