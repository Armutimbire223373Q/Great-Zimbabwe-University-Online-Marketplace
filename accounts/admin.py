from django.contrib import admin
from .models import CustomUser, Address, Notification

# Register your models here.
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'role', 'campus', 'is_active')
    list_filter = ('role', 'campus', 'is_active')
    search_fields = ('email', 'username', 'student_id')
    ordering = ('-date_joined',)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'street_address', 'city', 'is_default')
    list_filter = ('city', 'is_default')
    search_fields = ('street_address', 'city', 'user__email')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'message', 'user__email')
    ordering = ('-created_at',)
