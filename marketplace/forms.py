from django import forms
from .models import Listing, ListingImage, Report, Offer, EventGig
from django.forms import modelformset_factory
from accounts.models import CAMPUS_CHOICES

class ListingForm(forms.ModelForm):
    campus = forms.ChoiceField(choices=CAMPUS_CHOICES, required=False)
    condition = forms.ChoiceField(choices=[('new', 'New'), ('used', 'Used')], required=True)
    tags = forms.CharField(required=False, help_text='Comma-separated tags')
    location = forms.CharField(required=False, help_text='Dorm, block, or area')
    class Meta:
        model = Listing
        fields = ['title', 'category', 'description', 'price', 'status', 'image', 'premium', 'campus', 'condition', 'tags', 'location']

class ListingImageForm(forms.ModelForm):
    class Meta:
        model = ListingImage
        fields = ['image']

ListingImageFormSet = modelformset_factory(ListingImage, form=ListingImageForm, extra=3, can_delete=True)

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