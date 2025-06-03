from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Listing, ListingImage, Favorite, Cart, CartItem, Report, EventGig, Notification, Deal, Category, Purchase, ChatRoom, CommunityPost, Notice, DeliveryZone, DeliveryRequest, DeliveryRunner, ServiceProvider, ServiceRequest, SwapRequest, PaymentMethod, ChatMessage, Review, UserRating
from messaging.models import Conversation, Message
from .forms import ListingForm, ListingImageFormSet, ReportForm, EventGigForm, OfferForm, PaymentMethodForm
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from django.db import models, transaction
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.conf import settings
from .utils import (
    get_cart, get_cart_count, create_notification, generate_ecocash_qr, generate_mukuru_qr, get_payment_methods,
    generate_payment_reference
)
import logging
import traceback
import random
from django.views.decorators.csrf import ensure_csrf_cookie

# Get the custom user model
User = get_user_model()

# Set up logging
logger = logging.getLogger(__name__)

# Create your views here.

def listings(request):
    listings_qs = Listing.objects.select_related('owner').filter(status='active')
    paginator = Paginator(listings_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'listings': page_obj.object_list,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'paginator': paginator,
        'category_choices': Listing.CATEGORY_CHOICES,
    }
    return render(request, 'marketplace/listings.html', context)

@login_required
def listing_detail(request, pk):
    try:
        listing = get_object_or_404(Listing, pk=pk)
        is_favorite = False
        if request.user.is_authenticated:
            is_favorite = listing.favorited_by.filter(user=request.user).exists()
            
            # Add to recently viewed
            recently_viewed = request.session.get('recently_viewed', [])
            if pk not in recently_viewed:
                recently_viewed.insert(0, pk)
                recently_viewed = recently_viewed[:5]  # Keep only last 5
                request.session['recently_viewed'] = recently_viewed

        context = {
            'listing': listing,
            'is_favorite': is_favorite,
            'can_purchase': request.user.is_authenticated and request.user != listing.owner and listing.status == 'active'
        }
        return render(request, 'marketplace/listing_detail.html', context)
    except Exception as e:
        logger.error(f"Error in listing_detail view: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, 'An error occurred while loading the listing. Please try again.')
        return redirect('marketplace:listings')

@login_required
def swap_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    
    if request.method == 'POST':
        # Get the listing to swap with
        swap_listing_id = request.POST.get('swap_listing')
        swap_listing = get_object_or_404(Listing, pk=swap_listing_id)
        
        # Create swap request
        swap_request = SwapRequest.objects.create(
            requester=request.user,
            requested_listing=listing,
            offered_listing=swap_listing,
            status='pending'
        )
        
        messages.success(request, 'Swap request sent successfully!')
        return redirect('marketplace:swap_detail', pk=swap_request.pk)
    
    # Get user's active listings for swap
    user_listings = Listing.objects.filter(
        seller=request.user,
        status='active'
    ).exclude(pk=listing.pk)
    
    context = {
        'listing': listing,
        'user_listings': user_listings,
    }
    return render(request, 'marketplace/swap_listing.html', context)

@login_required
def create_listing(request):
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        formset = ListingImageFormSet(request.POST, request.FILES, queryset=ListingImage.objects.none())
        
        if form.is_valid() and formset.is_valid():
            # Check if there are any images before saving
            has_images = any(image_form.cleaned_data.get('image') for image_form in formset.forms)
            if not has_images and form.cleaned_data.get('status') == 'active':
                form.add_error(None, 'Active listings must have at least one image.')
                return render(request, 'marketplace/listing_form.html', {'form': form, 'formset': formset})
            
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            
            # Handle images
            for image_form in formset.cleaned_data:
                if image_form and not image_form.get('DELETE', False):
                    ListingImage.objects.create(listing=listing, image=image_form['image'])
            
            messages.success(request, 'Listing created successfully!')
            return redirect('marketplace:listing_detail', pk=listing.pk)
    else:
        form = ListingForm()
        formset = ListingImageFormSet(queryset=ListingImage.objects.none())
    return render(request, 'marketplace/listing_form.html', {'form': form, 'formset': formset})

@login_required
def edit_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.user != listing.owner:
        messages.error(request, 'You do not have permission to edit this listing.')
        return redirect('marketplace:listing_detail', pk=pk)
    
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing)
        formset = ListingImageFormSet(request.POST, request.FILES, queryset=listing.images.all())
        if form.is_valid() and formset.is_valid():
            form.save()
            
            # Handle images
            for image_form in formset:
                if image_form.cleaned_data.get('id') and image_form.cleaned_data.get('DELETE'):
                    image_form.cleaned_data['id'].delete()
                elif image_form.cleaned_data.get('image') and not image_form.cleaned_data.get('id'):
                    ListingImage.objects.create(listing=listing, image=image_form.cleaned_data['image'])
            
            messages.success(request, 'Listing updated successfully!')
            return redirect('marketplace:listing_detail', pk=listing.pk)
    else:
        form = ListingForm(instance=listing)
        formset = ListingImageFormSet(queryset=listing.images.all())
    return render(request, 'marketplace/listing_form.html', {'form': form, 'formset': formset})

@login_required
def delete_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.user != listing.owner:
        messages.error(request, 'You do not have permission to delete this listing.')
        return redirect('marketplace:listing_detail', pk=pk)
    if request.method == 'POST':
        listing.delete()
        messages.success(request, 'Listing deleted successfully!')
        return redirect('marketplace:listings')
    return render(request, 'marketplace/listing_confirm_delete.html', {'listing': listing})

def seller_listings(request, seller_id):
    seller = get_object_or_404(User, pk=seller_id)
    listings = Listing.objects.filter(owner=seller, status='active').order_by('-premium', '-created_at')
    return render(request, 'marketplace/seller_listings.html', {'seller': seller, 'listings': listings})

@login_required
def add_favorite(request, pk):
    """Add or remove a listing from favorites."""
    listing = get_object_or_404(Listing, pk=pk)
    
    if request.method != 'POST':
        messages.info(request, 'Please use the favorite button to add items to your favorites.')
        return redirect('marketplace:listing_detail', pk=pk)
    
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        listing=listing
    )
    
    if not created:
        favorite.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'removed'})
        messages.success(request, 'Listing removed from favorites.')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'added'})
        messages.success(request, 'Listing added to favorites.')
    
    return redirect('marketplace:listing_detail', pk=pk)

@require_http_methods(['POST'])
@login_required
def remove_favorite(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    Favorite.objects.filter(
        user=request.user,
        listing=listing
    ).delete()
    return JsonResponse({'status': 'removed'})

@login_required
def favorite_listings(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('listing')
    listings = [fav.listing for fav in favorites]
    return render(request, 'marketplace/favorite_listings.html', {'listings': listings})

@ensure_csrf_cookie
@require_http_methods(['POST'])
@login_required
def add_to_cart(request, listing_id):
    """Add a listing to the user's cart."""
    try:
        listing = get_object_or_404(Listing, pk=listing_id)
        
        # Check if user is trying to add their own listing
        if request.user == listing.owner:
            messages.error(request, 'You cannot add your own listing to the cart.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'You cannot add your own listing to the cart.'
                }, status=400)
            return redirect('marketplace:listing_detail', pk=listing_id)
        
        # Check if listing is active
        if listing.status != 'active':
            messages.error(request, 'This listing is no longer available.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'This listing is no longer available.'
                }, status=400)
            return redirect('marketplace:listing_detail', pk=listing_id)
        
        # Get or create cart for the user
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            listing=listing,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        messages.success(request, 'Item added to cart successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Added to cart!',
                'cart_count': get_cart_count(request)
            })
        return redirect('marketplace:cart')
            
    except Exception as e:
        logger.error(f"Error in add_to_cart view: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, 'An error occurred while adding to cart. Please try again.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while adding to cart. Please try again.'
            }, status=500)
        return redirect('marketplace:listing_detail', pk=listing_id)

def cart(request):
    """View cart items for both logged-in and unlogged users"""
    try:
        cart = get_cart(request)
        items = []
        total = 0
        
        if request.user.is_authenticated:
            # For authenticated users, get cart items with related listing data
            cart_items = CartItem.objects.filter(cart=cart).select_related('listing')
            for item in cart_items:
                items.append({
                    'listing': item.listing,
                    'quantity': item.quantity,
                    'total_price': item.listing.price * item.quantity
                })
                total += item.listing.price * item.quantity
        else:
            # For unauthenticated users, use session cart data
            for item in cart:
                total += item['price'] * item['quantity']
                items.append({
                    'listing': {
                        'id': item['listing_id'],
                        'title': item['title'],
                        'price': item['price'],
                        'image': {'url': item['image_url']} if 'image_url' in item else None
                    },
                    'quantity': item['quantity'],
                    'total_price': item['price'] * item['quantity']
                })
        
        context = {
            'items': items,
            'total': total,
            'is_authenticated': request.user.is_authenticated,
            'cart_count': get_cart_count(request)
        }
        return render(request, 'marketplace/cart.html', context)
    except Exception as e:
        logger.error(f"Error in cart view: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, 'An error occurred while loading your cart. Please try again.')
        return redirect('marketplace:listings')

@require_http_methods(['POST'])
def remove_from_cart(request, pk):
    try:
        if request.user.is_authenticated:
            cart = get_object_or_404(Cart, user=request.user)
            item = get_object_or_404(CartItem, cart=cart, listing_id=pk)
            item.delete()
        else:
            cart = request.session.get('cart', [])
            cart = [item for item in cart if item['listing_id'] != int(pk)]
            request.session['cart'] = cart
            request.session.modified = True
            
        return JsonResponse({
            'status': 'success',
            'message': 'Removed from cart!',
            'cart_count': get_cart_count(request)
        })
    except Exception as e:
        logger.error(f"Error in remove_from_cart: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to remove item from cart'
        }, status=400)

@require_http_methods(['POST'])
def update_cart_quantity(request, pk):
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
            
        if request.user.is_authenticated:
            cart = get_object_or_404(Cart, user=request.user)
            item = get_object_or_404(CartItem, cart=cart, listing_id=pk)
            item.quantity = quantity
            item.save()
        else:
            cart = request.session.get('cart', [])
            for item in cart:
                if item['listing_id'] == int(pk):
                    item['quantity'] = quantity
                    break
            request.session['cart'] = cart
            request.session.modified = True
            
        return JsonResponse({
            'status': 'success',
            'message': 'Cart updated!',
            'cart_count': get_cart_count(request)
        })
    except Exception as e:
        logger.error(f"Error in update_cart_quantity: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to update cart'
        }, status=400)

@login_required
def checkout(request):
    """Handle the checkout process"""
    try:
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            messages.error(request, 'Your cart is empty')
            return redirect('marketplace:cart')

        if request.method == 'POST':
            # Get payment method from form
            payment_method = request.POST.get('payment_method')
            if not payment_method:
                messages.error(request, 'Please select a payment method')
                return redirect('marketplace:checkout')

            # Create purchases for each item
            purchases = []
            for item in cart.items.all():
                # Generate a unique payment reference for each purchase
                payment_ref = generate_payment_reference()
                
                purchase = Purchase.objects.create(
                    buyer=request.user,
                    seller=item.listing.seller,
                    listing=item.listing,
                    quantity=item.quantity,
                    total_price=item.total_price,
                    payment_method=payment_method,
                    payment_reference=payment_ref,
                    status='pending'
                )
                purchases.append(purchase)

            # Clear the cart
            cart.items.all().delete()

            # Redirect to payment page
            return redirect('marketplace:payment', purchase_id=purchases[0].id)

        # Get user's payment methods
        payment_methods = PaymentMethod.objects.filter(user=request.user)
        
        context = {
            'cart': cart,
            'payment_methods': payment_methods,
        }
        return render(request, 'marketplace/checkout.html', context)

    except Exception as e:
        logger.error(f"Error during checkout: {str(e)}")
        messages.error(request, 'An error occurred while processing your purchase. Please try again.')
        return redirect('marketplace:cart')

def home(request):
    try:
        # Get categories
        categories = Category.objects.all()
        
        # Get featured listings (using premium instead of featured)
        try:
            featured_listings = Listing.objects.filter(
                status='active',
                premium=True
            ).select_related('owner').prefetch_related('images')[:6]
        except Exception as e:
            logger.error(f"Error getting featured listings: {str(e)}")
            featured_listings = []
        
        # Get latest listings
        try:
            latest_listings = Listing.objects.filter(
                status='active'
            ).select_related('owner').prefetch_related('images').order_by('-created_at')[:6]
        except Exception as e:
            logger.error(f"Error getting latest listings: {str(e)}")
            latest_listings = []
        
        # Get trending listings (based on favorites)
        try:
            trending_listings = Listing.objects.filter(
                status='active'
            ).select_related('owner').prefetch_related('images').annotate(
                favorite_count=Count('favorited_by')
            ).order_by('-favorite_count')[:6]
        except Exception as e:
            logger.error(f"Error getting trending listings: {str(e)}")
            trending_listings = []
        
        # Get hot deals (listings with lower prices)
        try:
            hot_deals = Listing.objects.filter(
                status='active'
            ).select_related('owner').prefetch_related('images').order_by('price')[:6]
        except Exception as e:
            logger.error(f"Error getting hot deals: {str(e)}")
            hot_deals = []
        
        # Get recently viewed listings
        recently_viewed = []
        if request.user.is_authenticated:
            try:
                recently_viewed_ids = request.session.get('recently_viewed', [])
                if recently_viewed_ids:
                    recently_viewed = Listing.objects.filter(
                        id__in=recently_viewed_ids,
                        status='active'
                    ).select_related('owner').prefetch_related('images')
            except Exception as e:
                logger.error(f"Error getting recently viewed listings: {str(e)}")
        
        # Get unread messages count
        unread_messages = 0
        if request.user.is_authenticated:
            try:
                unread_messages = Message.objects.filter(
                    recipient=request.user,
                    is_read=False
                ).count()
            except Exception as e:
                logger.error(f"Error getting unread messages count: {str(e)}")
        
        context = {
            'categories': categories,
            'featured_listings': featured_listings,
            'latest_listings': latest_listings,
            'trending_listings': trending_listings,
            'hot_deals': hot_deals,
            'recently_viewed': recently_viewed,
            'unread_messages': unread_messages,
        }
        
        return render(request, 'marketplace/home.html', context)
    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, 'An error occurred while loading the home page. Please try again.')
        return redirect('marketplace:listings')

@login_required
def report_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.reported_listing = listing
            report.save()
            messages.success(request, 'Thank you for your report. Our team will review it soon.')
            return redirect('marketplace:listing_detail', pk=pk)
    else:
        form = ReportForm()
    return render(request, 'marketplace/report_form.html', {'form': form, 'listing': listing})

@login_required
def report_user(request, user_id):
    reported_user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.reported_user = reported_user
            report.save()
            messages.success(request, 'Thank you for your report. Our team will review it soon.')
            return redirect('profile')
    else:
        form = ReportForm()
    return render(request, 'marketplace/report_form.html', {'form': form, 'reported_user': reported_user})

@login_required
def post_event_gig(request):
    if request.method == 'POST':
        form = EventGigForm(request.POST)
        if form.is_valid():
            event_gig = form.save(commit=False)
            event_gig.posted_by = request.user
            event_gig.save()
            messages.success(request, 'Your event/gig has been posted!')
            return redirect('browse_events_gigs')
    else:
        form = EventGigForm()
    return render(request, 'marketplace/eventgig_form.html', {'form': form})

def browse_events_gigs(request):
    events_gigs = EventGig.objects.order_by('-created_at')
    return render(request, 'marketplace/events_gigs.html', {'events_gigs': events_gigs})

def store(request, username):
    user = get_object_or_404(User, username=username)
    listings = Listing.objects.filter(owner=user, status='active')
    return render(request, 'marketplace/store.html', {'store_user': user, 'listings': listings})

@login_required
def notifications(request):
    notes = Notification.objects.filter(user=request.user).order_by('-created_at')
    notes.update(is_read=True)
    return render(request, 'marketplace/notifications.html', {'notifications': notes})

@login_required
def make_offer(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.listing = listing
            offer.sender = request.user
            offer.receiver = listing.owner
            offer.save()
            # Notify the seller
            create_notification(
                listing.owner,
                f'New offer for {listing.title} from {request.user.username}',
                url=reverse('marketplace:listing_detail', args=[listing.pk])
            )
            messages.success(request, 'Your offer has been sent to the seller.')
            return redirect('marketplace:listing_detail', pk=pk)
    else:
        form = OfferForm()
    return render(request, 'marketplace/offer_form.html', {'form': form, 'listing': listing})

@login_required
def confirm_deal(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    buyer = request.user
    seller = listing.owner
    deal, created = Deal.objects.get_or_create(listing=listing, buyer=buyer, seller=seller, status='pending')
    if request.method == 'POST':
        deal.status = 'confirmed'
        deal.confirmed_at = timezone.now()
        deal.save()
        listing.status = 'sold'
        listing.save()
        # Notify both parties
        create_notification(
            seller,
            f'Deal confirmed for {listing.title} with {buyer.username}',
            url=reverse('marketplace:listing_detail', args=[listing.pk])
        )
        create_notification(
            buyer,
            f'Deal confirmed for {listing.title} with {seller.username}',
            url=reverse('marketplace:listing_detail', args=[listing.pk])
        )
        messages.success(request, 'Deal confirmed! The listing is now marked as sold.')
        return redirect('marketplace:listing_detail', pk=pk)
    return render(request, 'marketplace/confirm_deal.html', {'deal': deal, 'listing': listing})

@login_required
def mark_listing_status(request, pk, status):
    listing = get_object_or_404(Listing, pk=pk)
    if request.user != listing.owner:
        messages.error(request, 'You do not have permission to change this listing status.')
        return redirect('marketplace:listing_detail', pk=pk)
    if status in ['active', 'sold']:
        listing.status = status
        listing.save()
        messages.success(request, f'Listing marked as {status}.')
    return redirect('marketplace:listing_detail', pk=pk)

def search(request):
    query = request.GET.get('q', '')
    if query:
        listings = Listing.objects.filter(
            status='active',
            title__icontains=query
        ).order_by('-premium', '-created_at')
    else:
        listings = Listing.objects.none()
    
    return render(request, 'marketplace/search_results.html', {
        'listings': listings,
        'query': query
    })

@login_required
@transaction.atomic
def purchase_listing(request, pk):
    try:
        listing = get_object_or_404(Listing, pk=pk)
        
        if request.user == listing.owner:
            messages.error(request, 'You cannot purchase your own listing.')
            return redirect('marketplace:listing_detail', pk=pk)
            
        if listing.status != 'active':
            messages.error(request, 'This listing is no longer available.')
            return redirect('marketplace:listing_detail', pk=pk)
    
        if request.method == 'POST':
            meetup_location = request.POST.get('meetup_location')
            meetup_time = request.POST.get('meetup_time')
            message = request.POST.get('message', '')
            
            if not meetup_location or not meetup_time:
                messages.error(request, 'Please provide both meetup location and time.')
                return redirect('marketplace:listing_detail', pk=pk)
            
            # Generate a unique payment reference
            while True:
                payment_ref = generate_payment_reference()
                if not Purchase.objects.filter(payment_reference=payment_ref).exists():
                    break
            
            # Create purchase record
            purchase = Purchase.objects.create(
                listing=listing,
                buyer=request.user,
                seller=listing.owner,
                price=listing.price,
                meetup_location=meetup_location,
                meetup_time=meetup_time,
                message=message,
                status='pending',
                payment_reference=payment_ref
            )
            
            # Create chat room for communication
            chat_room = ChatRoom.objects.create(
                listing=listing,
                buyer=request.user,
                seller=listing.owner
            )
        
            # Send notification to seller
            create_notification(
                listing.owner,
                f'New purchase request for {listing.title}',
                reverse('marketplace:purchase_detail', args=[purchase.id])
            )
            
            messages.success(request, 'Purchase request sent successfully!')
            return redirect('marketplace:purchase_detail', purchase_id=purchase.id)
            
        return render(request, 'marketplace/purchase_form.html', {'listing': listing})
        
    except Exception as e:
        logger.error(f"Error in purchase_listing view: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, 'An error occurred while processing your purchase. Please try again.')
        return redirect('marketplace:listing_detail', pk=pk)

@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    
    # Check if user is either buyer or seller
    if request.user != purchase.buyer and request.user != purchase.seller:
        messages.error(request, 'You do not have permission to view this purchase.')
        return redirect('marketplace:home')
    
    # Get or create chat room for this purchase
    chat_room, created = ChatRoom.objects.get_or_create(
        listing=purchase.listing,
        buyer=purchase.buyer,
        seller=purchase.seller
    )
    
    # Get messages for this chat room
    chat_messages = ChatMessage.objects.filter(chat_room=chat_room).order_by('created_at')
        
    return render(request, 'marketplace/purchase_detail.html', {
        'purchase': purchase,
        'chat_room': chat_room,
        'chat_messages': chat_messages
    })

@login_required
def request_delivery(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    
    if request.method == 'POST':
        delivery_zone = get_object_or_404(DeliveryZone, id=request.POST.get('delivery_zone'))
        delivery_request = DeliveryRequest.objects.create(
            listing=listing,
            buyer=request.user,
            pickup_location=request.POST.get('pickup_location'),
            delivery_location=request.POST.get('delivery_location'),
            delivery_zone=delivery_zone,
            delivery_fee=request.POST.get('delivery_fee'),
            notes=request.POST.get('notes', '')
        )
        messages.success(request, 'Delivery request created successfully!')
        return redirect('marketplace:delivery_detail', delivery_id=delivery_request.id)
    
    delivery_zones = DeliveryZone.objects.filter(
        campus=listing.owner.campus,
        is_active=True
    )
    return render(request, 'marketplace/request_delivery.html', {
        'listing': listing,
        'delivery_zones': delivery_zones
    })

@login_required
def become_runner(request):
    if request.method == 'POST':
        zones = request.POST.getlist('zones')
        runner = DeliveryRunner.objects.create(
            user=request.user,
            status='offline'
        )
        runner.zones.set(zones)
        messages.success(request, 'You are now registered as a delivery runner!')
        return redirect('marketplace:runner_dashboard')
    
    zones = DeliveryZone.objects.filter(
        campus=request.user.campus,
        is_active=True
    )
    return render(request, 'marketplace/become_runner.html', {'zones': zones})

@login_required
def list_service(request):
    if request.method == 'POST':
        service = ServiceProvider.objects.create(
            user=request.user,
            category=request.POST.get('category'),
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            hourly_rate=request.POST.get('hourly_rate'),
            fixed_rate=request.POST.get('fixed_rate')
        )
        messages.success(request, 'Your service has been listed!')
        return redirect('marketplace:service_detail', service_id=service.id)
    
    return render(request, 'marketplace/list_service.html')

@login_required
def request_service(request, service_id):
    service = get_object_or_404(ServiceProvider, id=service_id)
    
    if request.method == 'POST':
        service_request = ServiceRequest.objects.create(
            service=service,
            client=request.user,
            description=request.POST.get('description'),
            price=request.POST.get('price'),
            deadline=request.POST.get('deadline')
        )
        messages.success(request, 'Service request sent successfully!')
        return redirect('marketplace:service_request_detail', request_id=service_request.id)
    
    return render(request, 'marketplace/request_service.html', {'service': service})

@login_required
def request_swap(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    user_listings = Listing.objects.filter(
        owner=request.user,
        status='active'
    ).exclude(id=listing_id)
    
    if request.method == 'POST':
        offered_item = get_object_or_404(Listing, id=request.POST.get('offered_item'))
        swap_request = SwapRequest.objects.create(
            listing=listing,
            offered_item=offered_item,
            message=request.POST.get('message', '')
        )
        messages.success(request, 'Swap request sent successfully!')
        return redirect('marketplace:swap_detail', swap_id=swap_request.id)
    
    return render(request, 'marketplace/request_swap.html', {
        'listing': listing,
        'user_listings': user_listings
    })

@login_required
def payment_methods(request):
    """List and manage payment methods."""
    payment_methods = PaymentMethod.objects.filter(user=request.user)
    
    if request.method == 'POST':
        # Handle payment method deletion
        payment_method_id = request.POST.get('payment_method_id')
        if payment_method_id:
            payment_method = get_object_or_404(PaymentMethod, id=payment_method_id, user=request.user)
            payment_method.delete()
            messages.success(request, 'Payment method deleted successfully.')
            return redirect('marketplace:payment_methods')
    
    return render(request, 'marketplace/payment_methods.html', {
        'payment_methods': payment_methods
    })

@login_required
def add_payment_method(request):
    """Add a new payment method."""
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            payment_method = form.save(commit=False)
            payment_method.user = request.user
            payment_method.save()
            messages.success(request, 'Payment method added successfully.')
            return redirect('marketplace:checkout')
    else:
        form = PaymentMethodForm()
    
    return render(request, 'marketplace/add_payment_method.html', {'form': form})

@login_required
def delete_payment_method(request, pk):
    """Delete a payment method."""
    payment_method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)
    
    if request.method == 'POST':
        payment_method.delete()
        messages.success(request, 'Payment method deleted successfully.')
        return redirect('marketplace:payment_methods')
    
    return render(request, 'marketplace/delete_payment_method.html', {
        'payment_method': payment_method
    })

@login_required
def chat_room(request, user_id):
    """View chat room with another user."""
    other_user = get_object_or_404(User, id=user_id)
    
    # Get or create a conversation between the users
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user).first()
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    # Get messages for this conversation
    messages = Message.objects.filter(conversation=conversation).order_by('created_at')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                recipient=other_user,
                content=content
            )
            return redirect('marketplace:chat_room', user_id=user_id)
    
    return render(request, 'marketplace/chat_room.html', {
        'other_user': other_user,
        'messages': messages,
        'conversation': conversation
    })

@login_required
def send_message(request, user_id):
    """Send a message to another user."""
    recipient = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        content = request.POST.get('message')
        purchase_id = request.POST.get('purchase_id')
        
        if content:
            try:
                # Get or create conversation
                conversation = Conversation.objects.filter(
                    participants=request.user
                ).filter(
                    participants=recipient
                ).first()
                
                if not conversation:
                    conversation = Conversation.objects.create()
                    conversation.participants.add(request.user, recipient)
                
                # Create message
                message = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    recipient=recipient,
                    content=content
                )
                
                # Create notification for recipient
                create_notification(
                    recipient,
                    f'New message from {request.user.username}',
                    reverse('messaging:conversation', args=[conversation.id])
                )
                
                messages.success(request, 'Message sent successfully.')
                
                # If this is a purchase-related message, redirect back to purchase detail
                if purchase_id:
                    return redirect('marketplace:purchase_detail', pk=purchase_id)
                return redirect('messaging:conversation', conversation_id=conversation.id)
                
            except Exception as e:
                logger.error(f"Error sending message: {str(e)}")
                messages.error(request, 'Failed to send message. Please try again.')
                return redirect('marketplace:home')
    
    messages.error(request, 'Invalid request.')
    return redirect('marketplace:home')

@login_required
def my_listings(request):
    listings = Listing.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'marketplace/my_listings.html', {'listings': listings})

@login_required
def orders(request):
    """View for displaying user's orders."""
    # Get purchases where user is either buyer or seller
    purchases = Purchase.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).order_by('-created_at')
    
    context = {
        'purchases': purchases,
    }
    return render(request, 'marketplace/orders.html', context)

@login_required
def review_list(request):
    """List all reviews for the current user's listings."""
    reviews = Review.objects.filter(listing__seller=request.user)
    return render(request, 'marketplace/review_list.html', {
        'reviews': reviews
    })

@login_required
def review_create(request, listing_id):
    """Create a new review for a listing."""
    listing = get_object_or_404(Listing, id=listing_id)
    
    # Check if user has purchased the item
    if not Purchase.objects.filter(listing=listing, buyer=request.user, status='completed').exists():
        messages.error(request, 'You can only review items you have purchased.')
        return redirect('listing_detail', pk=listing_id)
    
    # Check if user has already reviewed
    if Review.objects.filter(listing=listing, reviewer=request.user).exists():
        messages.error(request, 'You have already reviewed this item.')
        return redirect('listing_detail', pk=listing_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            review = Review.objects.create(
                listing=listing,
                reviewer=request.user,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Review submitted successfully.')
            return redirect('listing_detail', pk=listing_id)
    
    return render(request, 'marketplace/review_create.html', {
        'listing': listing
    })

@login_required
def review_detail(request, pk):
    """View a specific review."""
    review = get_object_or_404(Review, pk=pk)
    return render(request, 'marketplace/review_detail.html', {
        'review': review
    })

@login_required
def edit_review(request, pk):
    """Edit an existing review."""
    review = get_object_or_404(Review, pk=pk)
    
    # Check if user is the reviewer
    if review.reviewer != request.user:
        messages.error(request, 'You can only edit your own reviews.')
        return redirect('review_detail', pk=pk)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            review.rating = rating
            review.comment = comment
            review.save()
            messages.success(request, 'Review updated successfully.')
            return redirect('review_detail', pk=pk)
    
    return render(request, 'marketplace/review_edit.html', {
        'review': review
    })

@login_required
def delete_review(request, pk):
    """Delete a review."""
    review = get_object_or_404(Review, pk=pk)
    
    # Check if user is the reviewer
    if review.reviewer != request.user:
        messages.error(request, 'You can only delete your own reviews.')
        return redirect('review_detail', pk=pk)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted successfully.')
        return redirect('review_list')
    
    return render(request, 'marketplace/review_delete.html', {
        'review': review
    })

def categories(request):
    """List all categories."""
    categories = Category.objects.all()
    return render(request, 'marketplace/categories.html', {
        'categories': categories
    })

def category_detail(request, pk):
    """View listings in a specific category."""
    category = get_object_or_404(Category, pk=pk)
    listings = Listing.objects.filter(category=category, is_active=True)
    return render(request, 'marketplace/category_detail.html', {
        'category': category,
        'listings': listings,
        'category_choices': Listing.CATEGORY_CHOICES,
    })

@login_required
def delivery_detail(request, pk):
    """View delivery details for a listing."""
    listing = get_object_or_404(Listing, pk=pk)
    delivery_requests = DeliveryRequest.objects.filter(listing=listing)
    
    if request.method == 'POST':
        # Handle delivery request creation
        delivery_zone = request.POST.get('delivery_zone')
        address = request.POST.get('address')
        
        if delivery_zone and address:
            delivery_request = DeliveryRequest.objects.create(
                listing=listing,
                buyer=request.user,
                delivery_zone_id=delivery_zone,
                delivery_address=address
            )
            messages.success(request, 'Delivery request submitted successfully.')
            return redirect('delivery_detail', pk=pk)
    
    return render(request, 'marketplace/delivery_detail.html', {
        'listing': listing,
        'delivery_requests': delivery_requests,
        'delivery_zones': DeliveryZone.objects.all()
    })

@login_required
def service_detail(request, pk):
    """View service details for a listing."""
    listing = get_object_or_404(Listing, pk=pk)
    service_requests = ServiceRequest.objects.filter(listing=listing)
    
    if request.method == 'POST':
        # Handle service request creation
        service_type = request.POST.get('service_type')
        description = request.POST.get('description')
        
        if service_type and description:
            service_request = ServiceRequest.objects.create(
                listing=listing,
                buyer=request.user,
                service_type=service_type,
                description=description
            )
            messages.success(request, 'Service request submitted successfully.')
            return redirect('service_detail', pk=pk)
    
    return render(request, 'marketplace/service_detail.html', {
        'listing': listing,
        'service_requests': service_requests,
        'service_providers': ServiceProvider.objects.all()
    })

@login_required
def swap_detail(request, pk):
    """View swap details for a listing."""
    listing = get_object_or_404(Listing, pk=pk)
    swap_requests = SwapRequest.objects.filter(listing=listing)
    
    if request.method == 'POST':
        # Handle swap request creation
        offered_listing_id = request.POST.get('offered_listing')
        message = request.POST.get('message')
        
        if offered_listing_id and message:
            offered_listing = get_object_or_404(Listing, id=offered_listing_id)
            swap_request = SwapRequest.objects.create(
                listing=listing,
                offered_listing=offered_listing,
                requester=request.user,
                message=message
            )
            messages.success(request, 'Swap request submitted successfully.')
            return redirect('swap_detail', pk=pk)
    
    return render(request, 'marketplace/swap_detail.html', {
        'listing': listing,
        'swap_requests': swap_requests,
        'user_listings': Listing.objects.filter(seller=request.user, is_active=True)
    })

@require_http_methods(['POST'])
def clear_cart(request):
    """Clear all items from the cart."""
    try:
        if request.user.is_authenticated:
            cart = get_object_or_404(Cart, user=request.user)
            cart.items.all().delete()
        else:
            request.session['cart'] = []
            request.session.modified = True
            
        return JsonResponse({
            'status': 'success',
            'message': 'Cart cleared successfully!',
            'cart_count': 0
        })
    except Exception as e:
        logger.error(f"Error in clear_cart: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to clear cart'
        }, status=400)

@login_required
def purchase_list(request):
    """View for displaying user's purchase history."""
    # Get purchases where user is either buyer or seller
    purchases = Purchase.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).select_related(
        'listing',
        'buyer',
        'seller'
    ).order_by('-created_at')
    
    context = {
        'purchases': purchases,
        'as_buyer': purchases.filter(buyer=request.user),
        'as_seller': purchases.filter(seller=request.user)
    }
    return render(request, 'marketplace/purchase_list.html', context)

@login_required
def cancel_purchase(request, pk):
    """Cancel a purchase request."""
    purchase = get_object_or_404(Purchase, pk=pk)
    
    # Check if user is either buyer or seller
    if request.user != purchase.buyer and request.user != purchase.seller:
        messages.error(request, 'You do not have permission to cancel this purchase.')
        return redirect('marketplace:purchase_list')
    
    # Check if purchase can be cancelled (only pending purchases can be cancelled)
    if purchase.status != 'pending':
        messages.error(request, 'This purchase cannot be cancelled.')
        return redirect('marketplace:purchase_list')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update purchase status
                purchase.status = 'cancelled'
                purchase.save()
                
                # Notify the other party
                other_party = purchase.seller if request.user == purchase.buyer else purchase.buyer
                create_notification(
                    other_party,
                    f'Purchase request for {purchase.listing.title} has been cancelled',
                    reverse('marketplace:purchase_detail', args=[purchase.id])
                )
                
                messages.success(request, 'Purchase request cancelled successfully.')
                return redirect('marketplace:purchase_list')
        except Exception as e:
            logger.error(f"Error cancelling purchase: {str(e)}")
            messages.error(request, 'An error occurred while cancelling the purchase.')
            return redirect('marketplace:purchase_list')
    
    return render(request, 'marketplace/cancel_purchase.html', {
        'purchase': purchase
    })

@login_required
def complete_purchase(request, pk):
    """Mark a purchase as completed."""
    purchase = get_object_or_404(Purchase, pk=pk)
    
    # Check if user is either buyer or seller
    if request.user != purchase.buyer and request.user != purchase.seller:
        messages.error(request, 'You do not have permission to complete this purchase.')
        return redirect('marketplace:purchase_list')
    
    # Check if purchase can be completed (only pending purchases can be completed)
    if purchase.status != 'pending':
        messages.error(request, 'This purchase cannot be completed.')
        return redirect('marketplace:purchase_list')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update purchase status
                purchase.status = 'completed'
                purchase.completed_at = timezone.now()
                purchase.save()
                
                # Update listing status if it's not already sold
                if purchase.listing.status == 'active':
                    purchase.listing.status = 'sold'
                    purchase.listing.save()
                
                # Notify the other party
                other_party = purchase.seller if request.user == purchase.buyer else purchase.buyer
                create_notification(
                    other_party,
                    f'Purchase for {purchase.listing.title} has been completed',
                    reverse('marketplace:purchase_detail', args=[purchase.id])
                )
                
                messages.success(request, 'Purchase marked as completed successfully.')
                return redirect('marketplace:purchase_list')
        except Exception as e:
            logger.error(f"Error completing purchase: {str(e)}")
            messages.error(request, 'An error occurred while completing the purchase.')
            return redirect('marketplace:purchase_list')
    
    return render(request, 'marketplace/complete_purchase.html', {
        'purchase': purchase
    })

@login_required
def rate_user(request, pk):
    """Rate a user after a completed purchase."""
    purchase = get_object_or_404(Purchase, pk=pk)
    
    # Check if user is either buyer or seller
    if request.user != purchase.buyer and request.user != purchase.seller:
        messages.error(request, 'You do not have permission to rate this user.')
        return redirect('marketplace:purchase_list')
    
    # Check if purchase is completed
    if purchase.status != 'completed':
        messages.error(request, 'You can only rate users after the purchase is completed.')
        return redirect('marketplace:purchase_list')
    
    # Determine which user to rate
    user_to_rate = purchase.seller if request.user == purchase.buyer else purchase.buyer
    
    # Check if user has already rated
    if UserRating.objects.filter(rater=request.user, rated_user=user_to_rate, purchase=purchase).exists():
        messages.error(request, 'You have already rated this user for this purchase.')
        return redirect('marketplace:purchase_list')
    
    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 0))
            comment = request.POST.get('comment', '')
            
            if 1 <= rating <= 5:
                with transaction.atomic():
                    # Create the rating
                    user_rating = UserRating.objects.create(
                        rater=request.user,
                        rated_user=user_to_rate,
                        purchase=purchase,
                        rating=rating,
                        comment=comment
                    )
                    
                    # Update user's average rating
                    user_to_rate.update_average_rating()
                    
                    # Notify the rated user
                    create_notification(
                        user_to_rate,
                        f'You received a {rating}-star rating from {request.user.username}',
                        reverse('marketplace:user_ratings', args=[user_to_rate.id])
                    )
                    
                    messages.success(request, 'Rating submitted successfully.')
                    return redirect('marketplace:purchase_list')
            else:
                messages.error(request, 'Rating must be between 1 and 5.')
        except Exception as e:
            logger.error(f"Error submitting rating: {str(e)}")
            messages.error(request, 'An error occurred while submitting the rating.')
            return redirect('marketplace:purchase_list')
    
    return render(request, 'marketplace/rate_user.html', {
        'purchase': purchase,
        'user_to_rate': user_to_rate
    })
