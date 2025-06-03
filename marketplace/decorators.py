from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

def seller_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('account_login')
        if not request.user.is_seller:
            messages.error(request, 'You must be a seller to access this page.')
            return redirect('marketplace:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def buyer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('account_login')
        if not request.user.is_buyer:
            messages.error(request, 'You must be a buyer to access this page.')
            return redirect('marketplace:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('account_login')
        obj = view_func.get_object()
        if obj.owner != request.user:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('marketplace:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def participant_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('account_login')
        obj = view_func.get_object()
        if request.user not in [obj.buyer, obj.seller]:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('marketplace:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view 