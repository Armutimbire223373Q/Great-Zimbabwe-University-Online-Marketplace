from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

# Campus choices moved to module level
CAMPUS_CHOICES = [
    ('main', 'Main Campus'),
    ('mashava', 'Mashava Campus'),
    ('mucheke', 'Mucheke Campus'),
]

class CustomUser(AbstractUser):
    STUDENT = 'student'
    STAFF = 'staff'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (STAFF, 'Staff'),
        (ADMIN, 'Admin'),
    ]
    
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    campus = models.CharField(max_length=20, choices=CAMPUS_CHOICES, default='main')
    phone_number = models.CharField(max_length=15, blank=True)
    student_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    gzu_email = models.EmailField(unique=True, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verification_document = models.FileField(upload_to='verification_docs/', blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    faculty = models.CharField(max_length=50, choices=[
        ('agriculture', 'Faculty of Agriculture'),
        ('arts', 'Faculty of Arts'),
        ('commerce', 'Faculty of Commerce'),
        ('education', 'Faculty of Education'),
        ('engineering', 'Faculty of Engineering'),
        ('law', 'Faculty of Law'),
        ('science', 'Faculty of Science'),
        ('social_sciences', 'Faculty of Social Sciences'),
    ], blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    year_of_study = models.PositiveSmallIntegerField(blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    preferred_contact = models.CharField(
        max_length=20,
        choices=[('whatsapp', 'WhatsApp'), ('phone', 'Phone'), ('email', 'Email')],
        default='whatsapp'
    )
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_ratings = models.PositiveIntegerField(default=0)
    is_blocked = models.BooleanField(default=False)
    last_active = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def get_rating_display(self):
        if self.total_ratings > 0:
            return f"{self.rating:.1f} ({self.total_ratings} ratings)"
        return "No ratings yet"

    def is_student_email(self):
        return self.email.endswith('@gzu.ac.zw')

    def verify_student(self):
        if self.is_student_email() or self.student_id:
            self.is_verified = True
            self.save()
            return True
        return False

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
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='account_notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
