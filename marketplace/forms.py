from django import forms
from .models import Listing, ListingImage, Report, Offer, EventGig, PaymentMethod
from django.forms import modelformset_factory
from accounts.models import CAMPUS_CHOICES

class ListingForm(forms.ModelForm):
    campus = forms.ChoiceField(choices=CAMPUS_CHOICES, required=False)
    condition = forms.ChoiceField(choices=Listing.CONDITION_CHOICES, required=True)
    category = forms.ChoiceField(choices=Listing.CATEGORY_CHOICES, required=True)
    tags = forms.CharField(required=False, help_text='Comma-separated tags')
    location = forms.CharField(required=False, help_text='Dorm, block, or area')
    
    class Meta:
        model = Listing
        fields = ['title', 'category', 'description', 'price', 'premium', 'campus', 'condition', 'tags', 'location']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }

class ListingImageForm(forms.ModelForm):
    class Meta:
        model = ListingImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'})
        }

ListingImageFormSet = modelformset_factory(
    ListingImage,
    form=ListingImageForm,
    extra=3,
    can_delete=True,
    max_num=3,
    min_num=1,
    validate_min=True
)

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the issue...'}),
        }

class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['amount', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional message...'}),
        }

class EventGigForm(forms.ModelForm):
    class Meta:
        model = EventGig
        fields = ['title', 'description', 'category', 'date', 'location', 'price']

class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['payment_type', 'account_number', 'account_name']
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
        } 