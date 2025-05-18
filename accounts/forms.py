from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, CAMPUS_CHOICES

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('.ac.zw'):
            raise forms.ValidationError('Please use your school (.ac.zw) email address.')
        return email
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    campus = forms.ChoiceField(choices=CAMPUS_CHOICES)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    profile_pic = forms.ImageField(required=False)
    class Meta:
        model = UserProfile
        fields = ['campus', 'contact_number', 'bio', 'profile_pic'] 