from django.conf import settings
from django.utils.html import strip_tags
import re
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, Notification, Purchase
import uuid
import time

def format_phone_number(phone):
    """Format phone number to international format for WhatsApp."""
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # If number starts with 0, replace with 263
    if phone.startswith('0'):
        phone = '263' + phone[1:]
    
    # If number doesn't start with country code, add it
    if not phone.startswith('263'):
        phone = '263' + phone
    
    return phone

def get_whatsapp_url(phone, message=None):
    """Generate WhatsApp URL for direct messaging."""
    phone = format_phone_number(phone)
    base_url = f"https://wa.me/{phone}"
    
    if message:
        # Clean and encode message
        message = strip_tags(message)
        message = message.replace('\n', '%0A')
        return f"{base_url}?text={message}"
    
    return base_url

def get_whatsapp_share_url(listing):
    """Generate WhatsApp share URL for a listing."""
    message = f"Check out this item on GZU Marketplace:\n\n"
    message += f"*{listing.title}*\n"
    message += f"Price: ${listing.price}\n"
    message += f"Location: {listing.location}\n\n"
    message += f"View details: {settings.SITE_URL}{listing.get_absolute_url()}"
    
    return get_whatsapp_url(settings.ADMIN_WHATSAPP, message)

def generate_ecocash_qr(amount, merchant_number, reference):
    """Generate EcoCash QR code data."""
    # Format: ecocash://pay?amount=10&merchant=0771234567&reference=ORDER123
    qr_data = f"ecocash://pay?amount={amount}&merchant={merchant_number}&reference={reference}"
    return qr_data

def generate_mukuru_qr(amount, recipient_number, reference):
    """Generate Mukuru QR code data."""
    # Format: mukuru://send?amount=10&recipient=0771234567&reference=ORDER123
    qr_data = f"mukuru://send?amount={amount}&recipient={recipient_number}&reference={reference}"
    return qr_data

def format_currency(amount):
    """Format amount in USD."""
    return f"${amount:,.2f}"

def get_cart(request):
    """Helper function to get cart for both logged-in and unlogged users"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        # For unlogged users, use session-based cart
        if 'cart' not in request.session:
            request.session['cart'] = []
        return request.session['cart']

def get_cart_count(request):
    """Helper function to get cart count for both logged-in and unlogged users"""
    if request.user.is_authenticated:
        cart = get_cart(request)
        return cart.items.count()
    else:
        cart = request.session.get('cart', [])
        return sum(item['quantity'] for item in cart)

def create_notification(user, message, url=None):
    """Create a notification for a user"""
    Notification.objects.create(user=user, message=message, url=url or '')

def get_payment_methods(user):
    """Get user's payment methods with QR codes."""
    from .models import PaymentMethod
    methods = PaymentMethod.objects.filter(user=user)
    
    for method in methods:
        if method.payment_type == 'ecocash':
            method.qr_data = generate_ecocash_qr(
                amount=0,  # Amount will be set at checkout
                merchant_number=method.account_number,
                reference=generate_payment_reference()
            )
        elif method.payment_type == 'mukuru':
            method.qr_data = generate_mukuru_qr(
                amount=0,  # Amount will be set at checkout
                recipient_number=method.account_number,
                reference=generate_payment_reference()
            )
    
    return methods

def generate_payment_reference(prefix='ORDER'):
    """Generate a unique payment reference"""
    # Generate a reference with timestamp to ensure uniqueness
    timestamp = int(time.time() * 1000)  # milliseconds
    reference = f"{prefix}-{timestamp}-{str(uuid.uuid4())[:8]}"
    
    # Check if reference exists, if so, generate a new one
    while Purchase.objects.filter(payment_reference=reference).exists():
        timestamp = int(time.time() * 1000)
        reference = f"{prefix}-{timestamp}-{str(uuid.uuid4())[:8]}"
    
    return reference 