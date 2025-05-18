from django.db import models
from django.contrib.auth.models import User
from accounts.models import CAMPUS_CHOICES
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.text import slugify

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # For FontAwesome icons
    
    class Meta:
        verbose_name_plural = 'Categories'
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

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
    
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
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
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
    
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
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
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s Cart"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ('cart', 'product')
    
    def __str__(self):
        return f"{self.quantity}x {self.product.title}"

class Wishlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    image = models.ImageField(upload_to='listing_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    premium = models.BooleanField(default=False, help_text='Premium listings are highlighted and shown first.')
    campus = models.CharField(max_length=100, choices=CAMPUS_CHOICES, blank=True, null=True)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='used')
    tags = models.CharField(max_length=200, blank=True, help_text='Comma-separated tags')
    location = models.CharField(max_length=100, blank=True, help_text='Dorm, block, or area')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('listing_detail', args=[str(self.pk)])

    def clean(self):
        if self.image:
            if self.image.size > 2*1024*1024:
                raise ValidationError('Image file too large (max 2MB).')
            if not self.image.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                raise ValidationError('Unsupported file type.')

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listing_images/')

    def __str__(self):
        return f"Image for {self.listing.title}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')

    def __str__(self):
        return f"{self.user.username} likes {self.listing.title}"

class Report(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_against', blank=True, null=True)
    reported_listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reports', blank=True, null=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolution_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.reported_listing:
            return f"Report on {self.reported_listing.title} by {self.reporter.username}"
        elif self.reported_user:
            return f"Report on {self.reported_user.username} by {self.reporter.username}"
        return f"Report by {self.reporter.username}"

class Deal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='deals')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deals_bought')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deals_sold')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Deal: {self.listing.title} ({self.buyer.username} & {self.seller.username})"

class Offer(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='offers')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offers_sent')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offers_received')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True)
    accepted = models.BooleanField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer: {self.amount} for {self.listing.title} from {self.sender.username} to {self.receiver.username}"

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
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events_gigs')
    date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.category})"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
