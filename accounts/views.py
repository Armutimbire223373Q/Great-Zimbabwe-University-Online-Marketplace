from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegisterForm, UserProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

# Create your views here.

def register(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.is_active = False  # Require email verification
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            # Send verification email
            current_site = get_current_site(request)
            subject = 'Activate your GZU Marketplace account'
            message = render_to_string('accounts/email_verification.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserRegisterForm()
        profile_form = UserProfileForm()
    return render(request, 'accounts/register.html', {'user_form': user_form, 'profile_form': profile_form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        user.userprofile.is_email_verified = True
        user.userprofile.save()
        messages.success(request, 'Your account has been verified. You can now log in.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')
        return redirect('login')

@login_required
def profile(request):
    try:
        profile = request.user.userprofile
    except ObjectDoesNotExist:
        from .models import UserProfile
        profile = UserProfile.objects.create(user=request.user, campus='', contact_number='')
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

@login_required
def edit_profile(request):
    profile = request.user.userprofile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'accounts/edit_profile.html', {'form': form})
