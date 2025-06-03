from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Listing, Category, Cart, CartItem, Purchase
from decimal import Decimal
import json

User = get_user_model()

class MarketplaceViewsTest(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )
        
        # Create test listing
        self.listing = Listing.objects.create(
            title='Test Listing',
            description='Test Description',
            price=Decimal('100.00'),
            category=self.category,
            owner=self.user1,
            status='active'
        )
        
        # Create test client
        self.client = Client()
    
    def test_home_view(self):
        """Test home view."""
        response = self.client.get(reverse('marketplace:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'marketplace/home.html')
    
    def test_listing_detail_view(self):
        """Test listing detail view."""
        response = self.client.get(reverse('marketplace:listing_detail', args=[self.listing.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'marketplace/listing_detail.html')
    
    def test_create_listing_view(self):
        """Test create listing view."""
        # Login required
        response = self.client.get(reverse('marketplace:create_listing'))
        self.assertEqual(response.status_code, 302)
        
        # Login and try again
        self.client.login(email='test1@example.com', password='testpass123')
        response = self.client.get(reverse('marketplace:create_listing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'marketplace/listing_form.html')
        
        # Create listing
        response = self.client.post(reverse('marketplace:create_listing'), {
            'title': 'New Listing',
            'description': 'New Description',
            'price': '200.00',
            'category': self.category.pk,
            'status': 'active'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Listing.objects.filter(title='New Listing').exists())
    
    def test_edit_listing_view(self):
        """Test edit listing view."""
        # Login required
        response = self.client.get(reverse('marketplace:edit_listing', args=[self.listing.pk]))
        self.assertEqual(response.status_code, 302)
        
        # Login and try again
        self.client.login(email='test1@example.com', password='testpass123')
        response = self.client.get(reverse('marketplace:edit_listing', args=[self.listing.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'marketplace/listing_form.html')
        
        # Edit listing
        response = self.client.post(reverse('marketplace:edit_listing', args=[self.listing.pk]), {
            'title': 'Updated Listing',
            'description': 'Updated Description',
            'price': '150.00',
            'category': self.category.pk,
            'status': 'active'
        })
        self.assertEqual(response.status_code, 302)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'Updated Listing')
    
    def test_delete_listing_view(self):
        """Test delete listing view."""
        # Login required
        response = self.client.get(reverse('marketplace:delete_listing', args=[self.listing.pk]))
        self.assertEqual(response.status_code, 302)
        
        # Login and try again
        self.client.login(email='test1@example.com', password='testpass123')
        response = self.client.get(reverse('marketplace:delete_listing', args=[self.listing.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'marketplace/listing_confirm_delete.html')
        
        # Delete listing
        response = self.client.post(reverse('marketplace:delete_listing', args=[self.listing.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Listing.objects.filter(pk=self.listing.pk).exists())
    
    def test_add_to_cart_view(self):
        """Test add to cart view."""
        # Login required
        response = self.client.post(reverse('marketplace:add_to_cart', args=[self.listing.pk]))
        self.assertEqual(response.status_code, 302)
        
        # Login and try again
        self.client.login(email='test2@example.com', password='testpass123')
        response = self.client.post(reverse('marketplace:add_to_cart', args=[self.listing.pk]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(CartItem.objects.filter(
            cart__user=self.user2,
            listing=self.listing
        ).exists())
    
    def test_cart_view(self):
        """Test cart view."""
        # Login required
        response = self.client.get(reverse('marketplace:cart'))
        self.assertEqual(response.status_code, 302)
        
        # Login and try again
        self.client.login(email='test2@example.com', password='testpass123')
        response = self.client.get(reverse('marketplace:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'marketplace/cart.html')
    
    def test_checkout_view(self):
        """Test checkout view."""
        # Login required
        response = self.client.get(reverse('marketplace:checkout'))
        self.assertEqual(response.status_code, 302)
        
        # Login and try again
        self.client.login(email='test2@example.com', password='testpass123')
        response = self.client.get(reverse('marketplace:checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'marketplace/checkout.html')
        
        # Create cart item
        cart = Cart.objects.create(user=self.user2)
        CartItem.objects.create(cart=cart, listing=self.listing, quantity=1)
        
        # Checkout
        response = self.client.post(reverse('marketplace:checkout'), {
            'meetup_location': 'Test Location',
            'meetup_time': '2024-03-20 10:00:00',
            'message': 'Test Message'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Purchase.objects.filter(
            listing=self.listing,
            buyer=self.user2,
            seller=self.user1
        ).exists())
    
    def test_purchase_listing_view(self):
        """Test purchase listing view."""
        # Login required
        response = self.client.get(reverse('marketplace:purchase_listing', args=[self.listing.pk]))
        self.assertEqual(response.status_code, 302)
        
        # Login and try again
        self.client.login(email='test2@example.com', password='testpass123')
        response = self.client.get(reverse('marketplace:purchase_listing', args=[self.listing.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'marketplace/purchase_form.html')
        
        # Purchase listing
        response = self.client.post(reverse('marketplace:purchase_listing', args=[self.listing.pk]), {
            'meetup_location': 'Test Location',
            'meetup_time': '2024-03-20 10:00:00',
            'message': 'Test Message'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Purchase.objects.filter(
            listing=self.listing,
            buyer=self.user2,
            seller=self.user1
        ).exists())
    
    def test_purchase_detail_view(self):
        """Test purchase detail view."""
        # Create purchase
        purchase = Purchase.objects.create(
            listing=self.listing,
            buyer=self.user2,
            seller=self.user1,
            price=self.listing.price,
            meetup_location='Test Location',
            meetup_time='2024-03-20 10:00:00',
            message='Test Message',
            status='pending'
        )
        
        # Login required
        response = self.client.get(reverse('marketplace:purchase_detail', args=[purchase.pk]))
        self.assertEqual(response.status_code, 302)
        
        # Login as buyer
        self.client.login(email='test2@example.com', password='testpass123')
        response = self.client.get(reverse('marketplace:purchase_detail', args=[purchase.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'marketplace/purchase_detail.html')
        
        # Login as seller
        self.client.login(email='test1@example.com', password='testpass123')
        response = self.client.get(reverse('marketplace:purchase_detail', args=[purchase.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'marketplace/purchase_detail.html')
        
        # Login as other user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.client.login(email='other@example.com', password='testpass123')
        response = self.client.get(reverse('marketplace:purchase_detail', args=[purchase.pk]))
        self.assertEqual(response.status_code, 302)
