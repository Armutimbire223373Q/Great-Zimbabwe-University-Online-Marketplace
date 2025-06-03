from django.db import models
from django.contrib.auth.models import User
from accounts.models import CAMPUS_CHOICES
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class (e.g., 'fa-book')")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('archived', 'Archived'),
    ]
    
    seller = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_negotiable = models.BooleanField(default=False)
    quantity = models.PositiveIntegerField(default=1)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'created_at']

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('product', 'reviewer')
        ordering = ['-created_at']

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    buyer = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.ForeignKey('accounts.Address', on_delete=models.SET_NULL, null=True)
    payment_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.id} by {self.buyer.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity}x {self.product.title}"

class Cart(models.Model):
    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s Cart"
    
    def get_total(self):
        return sum(item.listing.price * item.quantity for item in self.items.all())
    
    def get_item_count(self):
        return self.items.count()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    listing = models.ForeignKey('Listing', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('cart', 'listing')
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.quantity}x {self.listing.title}"
    
    def get_subtotal(self):
        return self.listing.price * self.quantity

class Wishlist(models.Model):
    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name='wishlists')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email}'s Wishlist"

class Listing(models.Model):
    CATEGORY_CHOICES = [
        ('books', 'Books'),
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing'),
        ('furniture', 'Furniture'),
        ('food', 'Food'),
        ('services', 'Services'),
        ('other', 'Other'),
    ]
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('expired', 'Expired'),
    ]
    owner = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    premium = models.BooleanField(default=False, help_text='Premium listings are highlighted and shown first.')
    campus = models.CharField(max_length=100, choices=CAMPUS_CHOICES, blank=True, null=True)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='used')
    tags = models.CharField(max_length=200, blank=True, help_text='Comma-separated tags')
    location = models.CharField(max_length=100, blank=True, help_text='Dorm, block, or area')
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('marketplace:listing_detail', args=[str(self.pk)])

    def clean(self):
        if self.pk and self.status == 'active' and not self.images.exists():
            raise ValidationError('Active listings must have at least one image.')

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listing_images/')

    def __str__(self):
        return f"Image for {self.listing.title}"

class Favorite(models.Model):
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='favorites')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')

    def __str__(self):
        return f"{self.user.email} favorited {self.listing.title}"

class Report(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    reporter = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='reports_against', blank=True, null=True)
    reported_listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reports', blank=True, null=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolution_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Report by {self.reporter.email} on {self.created_at}"

class Deal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='deals')
    buyer = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='deals_bought')
    seller = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='deals_sold')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Deal for {self.listing.title} between {self.buyer.email} and {self.seller.email}"

class Offer(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='offers')
    sender = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='offers_sent')
    receiver = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='offers_received')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True)
    accepted = models.BooleanField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer of {self.amount} from {self.sender.email} to {self.receiver.email}"

class EventGig(models.Model):
    CATEGORY_CHOICES = [
        ('event', 'Event'),
        ('gig', 'Gig'),
        ('job', 'Job'),
        ('ticket', 'Ticket'),
        ('other', 'Other'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    posted_by = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='events_gigs')
    date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Notification(models.Model):
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='marketplace_notifications')
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.email}: {self.message}"

class CommunityPost(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.author.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class Notice(models.Model):
    TYPE_CHOICES = [
        ('alert', 'Alert'),
        ('announcement', 'Announcement'),
        ('scam_warning', 'Scam Warning'),
        ('service_update', 'Service Update'),
        ('lost_found', 'Lost & Found'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    notice_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.get_notice_type_display()}: {self.title}"
    
    def is_current(self):
        now = timezone.now()
        if self.end_date:
            return self.start_date <= now <= self.end_date
        return self.start_date <= now

class UserRating(models.Model):
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Fair'),
        (3, 'Good'),
        (4, 'Very Good'),
        (5, 'Excellent'),
    ]
    
    rater = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='ratings_given')
    rated_user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='ratings_received')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    transaction = models.ForeignKey('Purchase', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('rater', 'rated_user', 'transaction')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rater.get_full_name()} rated {self.rated_user.get_full_name()} {self.rating}/5"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_user_rating()
    
    def update_user_rating(self):
        ratings = UserRating.objects.filter(rated_user=self.rated_user)
        total_ratings = ratings.count()
        avg_rating = ratings.aggregate(models.Avg('rating'))['rating__avg'] or 0
        
        self.rated_user.total_ratings = total_ratings
        self.rated_user.rating = round(avg_rating, 2)
        self.rated_user.save()

class DeliveryZone(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    campus = models.CharField(max_length=20, choices=CAMPUS_CHOICES)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_campus_display()})"

class DeliveryRunner(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]
    
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='delivery_runs')
    zones = models.ManyToManyField(DeliveryZone)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_deliveries = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Runner: {self.user.get_full_name()}"

class DeliveryRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='deliveries')
    buyer = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='delivery_requests')
    runner = models.ForeignKey(DeliveryRunner, on_delete=models.SET_NULL, null=True, blank=True)
    pickup_location = models.CharField(max_length=200)
    delivery_location = models.CharField(max_length=200)
    delivery_zone = models.ForeignKey(DeliveryZone, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Delivery for {self.listing.title}"

class ServiceProvider(models.Model):
    CATEGORY_CHOICES = [
        ('tutoring', 'Tutoring'),
        ('typing', 'Typing & Printing'),
        ('design', 'Graphic Design'),
        ('hairdressing', 'Hairdressing'),
        ('other', 'Other Services'),
    ]
    
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='services')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fixed_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_jobs = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} by {self.user.get_full_name()}"

class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    service = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='requests')
    client = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='service_requests')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Request for {self.service.title}"

class SwapRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='swap_requests')
    offered_item = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='swap_offers')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Swap request: {self.offered_item.title} for {self.listing.title}"

class PaymentMethod(models.Model):
    PAYMENT_TYPES = [
        ('ecocash', 'EcoCash'),
        ('mukuru', 'Mukuru'),
        ('cash', 'USD Cash'),
    ]
    
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    qr_code = models.ImageField(upload_to='payment_qr_codes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.account_number}"

class Purchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='purchases')
    buyer = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='purchases')
    seller = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='sales')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    payment_reference = models.CharField(max_length=50, unique=True)
    meetup_location = models.CharField(max_length=200, blank=True)
    meetup_time = models.DateTimeField(null=True, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Purchase of {self.listing.title} by {self.buyer.get_full_name()}"
    
    def get_absolute_url(self):
        return reverse('marketplace:purchase_detail', args=[str(self.id)])

class ChatRoom(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='chat_rooms')
    buyer = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='buyer_chats')
    seller = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='seller_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('listing', 'buyer', 'seller')
    
    def __str__(self):
        return f"Chat for {self.listing.title} between {self.buyer.get_full_name()} and {self.seller.get_full_name()}"

class ChatMessage(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='marketplace_sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"
