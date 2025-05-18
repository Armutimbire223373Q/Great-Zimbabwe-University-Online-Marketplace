from django.contrib import admin
from .models import Listing, ListingImage, Favorite, Review, Cart, CartItem, Report, Deal, Offer, EventGig, Notification

# Register your models here.
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'price', 'status', 'premium', 'created_at')
    list_filter = ('category', 'status', 'premium')

admin.site.register(Listing, ListingAdmin)
admin.site.register(ListingImage)
admin.site.register(Favorite)
admin.site.register(Review)
admin.site.register(Cart)
admin.site.register(CartItem)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'reported_user', 'reported_listing', 'status', 'created_at', 'resolved_at')
    list_filter = ('status', 'created_at')
    search_fields = ('reason',)

admin.site.register(Deal)
admin.site.register(Offer)
admin.site.register(EventGig)
admin.site.register(Notification)
