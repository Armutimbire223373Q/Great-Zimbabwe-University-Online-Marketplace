from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Listing, ListingImage, Favorite, Cart, CartItem, Report, EventGig, Notification, Deal
from .forms import ListingForm, ListingImageFormSet, ReportForm, EventGigForm, OfferForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.utils import timezone

# Create your views here.

def listings(request):
    listings_qs = Listing.objects.select_related('owner').prefetch_related('reviews').filter(status='active')
    paginator = Paginator(listings_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'listings': page_obj.object_list,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'paginator': paginator,
    }
    return render(request, 'marketplace/listings.html', context)

def listing_detail(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = listing.favorited_by.filter(user=request.user).exists()
    return render(request, 'marketplace/listing_detail.html', {'listing': listing, 'is_favorite': is_favorite})

@login_required
def create_listing(request):
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        formset = ListingImageFormSet(request.POST, request.FILES, queryset=ListingImage.objects.none())
        if form.is_valid() and formset.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            for image_form in formset.cleaned_data:
                if image_form and not image_form.get('DELETE', False):
                    ListingImage.objects.create(listing=listing, image=image_form['image'])
            messages.success(request, 'Listing created successfully!')
            return redirect('listings')
    else:
        form = ListingForm()
        formset = ListingImageFormSet(queryset=ListingImage.objects.none())
    return render(request, 'marketplace/listing_form.html', {'form': form, 'formset': formset})

@login_required
def edit_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.user != listing.owner:
        messages.error(request, 'You do not have permission to edit this listing.')
        return redirect('listing_detail', pk=pk)
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing)
        formset = ListingImageFormSet(request.POST, request.FILES, queryset=listing.images.all())
        if form.is_valid() and formset.is_valid():
            form.save()
            for image_form in formset:
                if image_form.cleaned_data.get('id') and image_form.cleaned_data.get('DELETE'):
                    image_form.cleaned_data['id'].delete()
                elif image_form.cleaned_data.get('image') and not image_form.cleaned_data.get('id'):
                    ListingImage.objects.create(listing=listing, image=image_form.cleaned_data['image'])
            messages.success(request, 'Listing updated successfully!')
            return redirect('listing_detail', pk=listing.pk)
    else:
        form = ListingForm(instance=listing)
        formset = ListingImageFormSet(queryset=listing.images.all())
    return render(request, 'marketplace/listing_form.html', {'form': form, 'formset': formset})

@login_required
def delete_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.user != listing.owner:
        messages.error(request, 'You do not have permission to delete this listing.')
        return redirect('listing_detail', pk=pk)
    if request.method == 'POST':
        listing.delete()
        messages.success(request, 'Listing deleted successfully!')
        return redirect('listings')
    return render(request, 'marketplace/listing_confirm_delete.html', {'listing': listing})

def seller_listings(request, seller_id):
    seller = get_object_or_404(User, pk=seller_id)
    listings = Listing.objects.filter(owner=seller, status='active').order_by('-premium', '-created_at')
    return render(request, 'marketplace/seller_listings.html', {'seller': seller, 'listings': listings})

@login_required
def add_favorite(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    Favorite.objects.get_or_create(user=request.user, listing=listing)
    messages.success(request, 'Added to your favorites!')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('listings')))

@login_required
def remove_favorite(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    Favorite.objects.filter(user=request.user, listing=listing).delete()
    messages.success(request, 'Removed from your favorites!')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('listings')))

@login_required
def favorite_listings(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('listing')
    listings = [fav.listing for fav in favorites]
    return render(request, 'marketplace/favorite_listings.html', {'listings': listings})

@login_required
def add_to_cart(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    cart, created = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, listing=listing)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, 'Added to cart!')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('listings')))

@login_required
def remove_from_cart(request, pk):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, cart=cart, listing_id=pk)
    item.delete()
    messages.success(request, 'Removed from cart!')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('view_cart')))

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('listing')
    total = sum(item.listing.price * item.quantity for item in items)
    return render(request, 'marketplace/cart.html', {'cart': cart, 'items': items, 'total': total})

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.select_related('listing')
    total = sum(item.listing.price * item.quantity for item in items)
    if request.method == 'POST':
        # Simulate checkout (clear cart)
        cart.items.all().delete()
        messages.success(request, 'Checkout complete! (Payment simulated)')
        return redirect('listings')
    return render(request, 'marketplace/checkout.html', {'cart': cart, 'items': items, 'total': total})

def home(request):
    from .models import Listing
    listings = Listing.objects.filter(status='active').order_by('-premium', '-created_at')[:6]
    return render(request, 'home.html', {'listings': listings})

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
            return redirect('listing_detail', pk=pk)
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

def create_notification(user, message, url=None):
    Notification.objects.create(user=user, message=message, url=url or '')

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
                url=reverse('listing_detail', args=[listing.pk])
            )
            messages.success(request, 'Your offer has been sent to the seller.')
            return redirect('listing_detail', pk=pk)
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
            url=reverse('listing_detail', args=[listing.pk])
        )
        create_notification(
            buyer,
            f'Deal confirmed for {listing.title} with {seller.username}',
            url=reverse('listing_detail', args=[listing.pk])
        )
        messages.success(request, 'Deal confirmed! The listing is now marked as sold.')
        return redirect('listing_detail', pk=pk)
    return render(request, 'marketplace/confirm_deal.html', {'deal': deal, 'listing': listing})

@login_required
def mark_listing_status(request, pk, status):
    listing = get_object_or_404(Listing, pk=pk)
    if request.user != listing.owner:
        messages.error(request, 'You do not have permission to change this listing status.')
        return redirect('listing_detail', pk=pk)
    if status in ['active', 'sold']:
        listing.status = status
        listing.save()
        messages.success(request, f'Listing marked as {status}.')
    return redirect('listing_detail', pk=pk)
