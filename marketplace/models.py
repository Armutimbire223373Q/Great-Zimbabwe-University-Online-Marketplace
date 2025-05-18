from django.db import models
from django.contrib.auth.models import User
from accounts.models import CAMPUS_CHOICES
from django.urls import reverse
from django.core.exceptions import ValidationError

# Create your models here.

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

class Review(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('listing', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating}★ by {self.user.username} on {self.listing.title}"

    def get_absolute_url(self):
        return reverse('listing_detail', args=[str(self.listing.pk)])

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.listing.title} in {self.cart.user.username}'s cart"

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
