from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from .models import Listing, Category, Cart, CartItem, Purchase, Review

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[
        RegexValidator(
            regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            message='Enter a valid email address.'
        )
    ])
    first_name = serializers.CharField(
        min_length=2,
        max_length=30,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s-]+$',
                message='First name can only contain letters, spaces, and hyphens.'
            )
        ]
    )
    last_name = serializers.CharField(
        min_length=2,
        max_length=30,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s-]+$',
                message='Last name can only contain letters, spaces, and hyphens.'
            )
        ]
    )
    phone_number = serializers.CharField(
        required=False,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{10}$',
                message='Enter a valid 10-digit phone number.'
            )
        ]
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'is_seller', 'is_buyer', 'date_joined', 'profile_image'
        ]
        read_only_fields = ['id', 'date_joined']

class CategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        min_length=2,
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s-]+$',
                message='Category name can only contain letters, numbers, spaces, and hyphens.'
            )
        ]
    )
    slug = serializers.SlugField(
        min_length=2,
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^[a-z0-9-]+$',
                message='Slug can only contain lowercase letters, numbers, and hyphens.'
            )
        ]
    )

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'slug', 'parent_category', 'image']
        read_only_fields = ['id']

    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError('A category with this name already exists.')
        return value

    def validate_slug(self, value):
        if Category.objects.filter(slug=value).exists():
            raise serializers.ValidationError('A category with this slug already exists.')
        return value

class ListingSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source='category'
    )
    title = serializers.CharField(
        min_length=5,
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-_.,!?()]+$',
                message='Title contains invalid characters.'
            )
        ]
    )
    description = serializers.CharField(min_length=20, max_length=2000)
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    status = serializers.ChoiceField(choices=Listing.STATUS_CHOICES)
    images = serializers.SerializerMethodField()
    location = serializers.CharField(required=False, max_length=200)
    condition = serializers.ChoiceField(choices=Listing.CONDITION_CHOICES, required=False)
    quantity = serializers.IntegerField(
        required=False,
        validators=[MinValueValidator(1)],
        default=1
    )

    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'price', 'category', 'category_id',
            'owner', 'status', 'created_at', 'updated_at', 'images',
            'location', 'condition', 'quantity'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_images(self, obj):
        return [image.image.url for image in obj.images.all()]

    def validate(self, data):
        if data.get('status') == 'active' and not self.context.get('images'):
            raise serializers.ValidationError('Active listings must have at least one image.')
        return data

class CartItemSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.filter(status='active'),
        write_only=True,
        source='listing'
    )
    quantity = serializers.IntegerField(
        validators=[MinValueValidator(1)],
        default=1
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'listing', 'listing_id', 'quantity', 'subtotal', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_subtotal(self, obj):
        return obj.listing.price * obj.quantity

    def validate(self, data):
        if data['listing'].owner == self.context['request'].user:
            raise serializers.ValidationError('You cannot add your own listings to cart.')
        if data['quantity'] > data['listing'].quantity:
            raise serializers.ValidationError('Quantity exceeds available stock.')
        return data

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    currency = serializers.CharField(default='USD')

    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'items', 'total', 'item_count', 'currency',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_total(self, obj):
        return sum(item.listing.price * item.quantity for item in obj.items.all())

    def get_item_count(self, obj):
        return obj.items.count()

    def validate(self, data):
        if self.instance and self.instance.items.count() >= 20:
            raise serializers.ValidationError('Cart cannot contain more than 20 items.')
        return data

class PurchaseSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    buyer = UserSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    meetup_time = serializers.DateTimeField()
    meetup_location = serializers.CharField(max_length=200)
    status = serializers.ChoiceField(choices=Purchase.STATUS_CHOICES)
    payment_status = serializers.CharField()
    payment_method = serializers.CharField()
    tracking_number = serializers.CharField(required=False, max_length=50)
    delivery_status = serializers.CharField()

    class Meta:
        model = Purchase
        fields = [
            'id', 'listing', 'buyer', 'seller', 'price', 'status',
            'meetup_location', 'meetup_time', 'message', 'created_at',
            'payment_status', 'payment_method', 'tracking_number',
            'delivery_status'
        ]
        read_only_fields = ['id', 'listing', 'buyer', 'seller', 'price', 'created_at']

    def validate_meetup_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError('Meetup time must be in the future.')
        return value

    def validate(self, data):
        if data['status'] == 'completed' and data['payment_status'] != 'paid':
            raise serializers.ValidationError('Purchase cannot be completed without payment.')
        return data

class ReviewSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)
    reviewed = UserSerializer(read_only=True)
    rating = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = serializers.CharField(min_length=10, max_length=1000)
    helpful_count = serializers.IntegerField(read_only=True)
    response = serializers.CharField(required=False, max_length=1000)

    class Meta:
        model = Review
        fields = [
            'id', 'reviewer', 'reviewed', 'rating', 'comment',
            'created_at', 'updated_at', 'helpful_count', 'response'
        ]
        read_only_fields = ['id', 'reviewer', 'reviewed', 'created_at', 'updated_at', 'helpful_count']

    def validate(self, data):
        if self.context['request'].user == data['reviewed']:
            raise serializers.ValidationError('You cannot review yourself.')
        if Review.objects.filter(reviewer=self.context['request'].user, reviewed=data['reviewed']).exists():
            raise serializers.ValidationError('You have already reviewed this user.')
        return data 