from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    STUDENT = 'student'
    STAFF = 'staff'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (STAFF, 'Staff'),
        (ADMIN, 'Admin'),
    ]
    
    CAMPUS_CHOICES = [
        ('main', 'Main Campus'),
        ('mashava', 'Mashava Campus'),
        ('mucheke', 'Mucheke Campus'),
    ]
    
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    campus = models.CharField(max_length=20, choices=CAMPUS_CHOICES, default='main')
    phone_number = models.CharField(max_length=15, blank=True)
    student_id = models.CharField(max_length=20, blank=True)
    is_email_verified = models.BooleanField(default=False)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f"{self.street_address}, {self.city}"

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
