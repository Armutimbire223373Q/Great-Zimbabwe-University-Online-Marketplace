from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, CAMPUS_CHOICES

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    campus = forms.ChoiceField(choices=CAMPUS_CHOICES)
    phone_number = forms.CharField(max_length=15, required=False)
    student_id = forms.CharField(max_length=20, required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    profile_picture = forms.ImageField(required=False)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('.ac.zw'):
            raise forms.ValidationError('Please use your school (.ac.zw) email address.')
        return email

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'campus', 
                 'phone_number', 'student_id', 'bio', 'profile_picture', 
                 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    campus = forms.ChoiceField(choices=CAMPUS_CHOICES)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    profile_picture = forms.ImageField(required=False)
    
    class Meta:
        model = CustomUser
        fields = ['campus', 'phone_number', 'bio', 'profile_picture'] 