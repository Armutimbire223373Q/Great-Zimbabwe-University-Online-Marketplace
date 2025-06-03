from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import Listing, Category, Cart, CartItem, Purchase, Review

User = get_user_model()

class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.seller = User.objects.create_user(
            email='seller@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Seller',
            is_seller=True
        )
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description',
            slug='test-category'
        )
        self.listing = Listing.objects.create(
            title='Test Listing',
            description='Test Description',
            price=100.00,
            category=self.category,
            owner=self.seller,
            status='active'
        )
        self.client.force_authenticate(user=self.user)

class CategoryAPITests(APITestCase):
    def test_list_categories(self):
        url = reverse('marketplace:category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_category(self):
        url = reverse('marketplace:category-list')
        data = {
            'name': 'New Category',
            'description': 'New Description',
            'slug': 'new-category'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 2)

    def test_get_subcategories(self):
        subcategory = Category.objects.create(
            name='Subcategory',
            description='Subcategory Description',
            slug='subcategory',
            parent_category=self.category
        )
        url = reverse('marketplace:category-subcategories', args=[self.category.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class ListingAPITests(APITestCase):
    def test_list_listings(self):
        url = reverse('marketplace:listing-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_listing(self):
        url = reverse('marketplace:listing-list')
        data = {
            'title': 'New Listing',
            'description': 'New Description',
            'price': 200.00,
            'category_id': self.category.id,
            'status': 'active'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Listing.objects.count(), 2)

    def test_add_to_cart(self):
        url = reverse('marketplace:listing-add-to-cart', args=[self.listing.id])
        data = {'quantity': 1}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CartItem.objects.count(), 1)

class CartAPITests(APITestCase):
    def setUp(self):
        super().setUp()
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            listing=self.listing,
            quantity=1
        )

    def test_get_cart(self):
        url = reverse('marketplace:cart-detail', args=[self.cart.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)

    def test_update_cart_item(self):
        url = reverse('marketplace:cart-update-item', args=[self.cart.id])
        data = {
            'item_id': self.cart_item.id,
            'quantity': 2
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 2)

    def test_remove_cart_item(self):
        url = reverse('marketplace:cart-remove-item', args=[self.cart.id])
        data = {'item_id': self.cart_item.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_checkout(self):
        url = reverse('marketplace:cart-checkout', args=[self.cart.id])
        data = {
            'meetup_location': 'Test Location',
            'meetup_time': '2024-03-20T10:00:00Z',
            'message': 'Test Message'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Purchase.objects.count(), 1)
        self.assertEqual(CartItem.objects.count(), 0)

class PurchaseAPITests(APITestCase):
    def setUp(self):
        super().setUp()
        self.purchase = Purchase.objects.create(
            listing=self.listing,
            buyer=self.user,
            seller=self.seller,
            price=100.00,
            meetup_location='Test Location',
            meetup_time='2024-03-20T10:00:00Z',
            message='Test Message'
        )

    def test_list_purchases(self):
        url = reverse('marketplace:purchase-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_purchase_status(self):
        url = reverse('marketplace:purchase-update-status', args=[self.purchase.id])
        data = {'status': 'completed'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # Only seller can update

        # Test as seller
        self.client.force_authenticate(user=self.seller)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.purchase.refresh_from_db()
        self.assertEqual(self.purchase.status, 'completed')

class ReviewAPITests(APITestCase):
    def test_create_review(self):
        url = reverse('marketplace:review-list')
        data = {
            'reviewed': self.seller.id,
            'rating': 5,
            'comment': 'Great seller!'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)

    def test_mark_helpful(self):
        review = Review.objects.create(
            reviewer=self.user,
            reviewed=self.seller,
            rating=5,
            comment='Great seller!'
        )
        url = reverse('marketplace:review-mark-helpful', args=[review.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.helpful_count, 1)

    def test_respond_to_review(self):
        review = Review.objects.create(
            reviewer=self.user,
            reviewed=self.seller,
            rating=5,
            comment='Great seller!'
        )
        url = reverse('marketplace:review-respond', args=[review.id])
        data = {'response': 'Thank you!'}
        
        # Test as non-reviewed user
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test as reviewed user
        self.client.force_authenticate(user=self.seller)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.response, 'Thank you!') 