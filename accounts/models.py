from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

CAMPUS_CHOICES = [
    ('Masvingo-Main Campus', 'Masvingo-Main Campus'),
    ('Mucheke Campus', 'Mucheke Campus'),
    ('Masvingo-City Campus', 'Masvingo-City Campus'),
    ('Mashava Campus', 'Mashava Campus'),
    ('Harare Campus', 'Harare Campus'),
    ('Bulawayo Campus', 'Bulawayo Campus'),
    ('Chiredzi Cohort', 'Chiredzi Cohort'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    campus = models.CharField(max_length=100, choices=CAMPUS_CHOICES)
    contact_number = models.CharField(max_length=20)
    bio = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    rating = models.FloatField(default=0)
    is_email_verified = models.BooleanField(default=False)
    # Add more fields as needed

    def __str__(self):
        return f"{self.user.username} Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance, defaults={'campus': '', 'contact_number': ''})
