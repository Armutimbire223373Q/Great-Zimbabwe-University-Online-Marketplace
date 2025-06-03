from django.core.management.base import BaseCommand
from django.core.files import File
from marketplace.models import Listing, ListingImage, Category
from accounts.models import CustomUser
import os
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Populates the database with test listings using existing images'

    def create_test_users(self):
        # First, remove all existing users except superusers
        CustomUser.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS('Removed existing non-superuser users'))
        
        test_users = [
            {
                'username': 'john_doe',
                'email': 'john.doe@example.ac.zw',
                'password': 'testpass123',
                'first_name': 'John',
                'last_name': 'Doe',
                'campus': 'main',
                'phone_number': '0771234567',
                'student_id': 'GZU2024001',
                'role': 'student'
            },
            {
                'username': 'jane_smith',
                'email': 'jane.smith@example.ac.zw',
                'password': 'testpass123',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'campus': 'mashava',
                'phone_number': '0772345678',
                'student_id': 'GZU2024002',
                'role': 'student'
            },
            {
                'username': 'prof_wilson',
                'email': 'wilson@example.ac.zw',
                'password': 'testpass123',
                'first_name': 'Robert',
                'last_name': 'Wilson',
                'campus': 'main',
                'phone_number': '0773456789',
                'student_id': 'GZU2024003',
                'role': 'staff'
            },
            {
                'username': 'mary_jones',
                'email': 'mary.jones@example.ac.zw',
                'password': 'testpass123',
                'first_name': 'Mary',
                'last_name': 'Jones',
                'campus': 'mucheke',
                'phone_number': '0774567890',
                'student_id': 'GZU2024004',
                'role': 'student'
            },
            {
                'username': 'david_brown',
                'email': 'david.brown@example.ac.zw',
                'password': 'testpass123',
                'first_name': 'David',
                'last_name': 'Brown',
                'campus': 'main',
                'phone_number': '0775678901',
                'student_id': 'GZU2024005',
                'role': 'student'
            },
            {
                'username': 'sarah_wilson',
                'email': 'sarah.wilson@example.ac.zw',
                'password': 'testpass123',
                'first_name': 'Sarah',
                'last_name': 'Wilson',
                'campus': 'mashava',
                'phone_number': '0776789012',
                'student_id': 'GZU2024006',
                'role': 'student'
            },
            {
                'username': 'mike_taylor',
                'email': 'mike.taylor@example.ac.zw',
                'password': 'testpass123',
                'first_name': 'Mike',
                'last_name': 'Taylor',
                'campus': 'mucheke',
                'phone_number': '0777890123',
                'student_id': 'GZU2024007',
                'role': 'student'
            },
            {
                'username': 'lisa_anderson',
                'email': 'lisa.anderson@example.ac.zw',
                'password': 'testpass123',
                'first_name': 'Lisa',
                'last_name': 'Anderson',
                'campus': 'main',
                'phone_number': '0778901234',
                'student_id': 'GZU2024008',
                'role': 'student'
            },
            {
                'username': 'james_miller',
                'email': 'james.miller@example.ac.zw',
                'password': 'testpass123',
                'first_name': 'James',
                'last_name': 'Miller',
                'campus': 'mashava',
                'phone_number': '0779012345',
                'student_id': 'GZU2024009',
                'role': 'student'
            },
            {
                'username': 'emma_davis',
                'email': 'emma.davis@example.ac.zw',
                'password': 'testpass123',
                'first_name': 'Emma',
                'last_name': 'Davis',
                'campus': 'mucheke',
                'phone_number': '0770123456',
                'student_id': 'GZU2024010',
                'role': 'student'
            }
        ]
        
        users = []
        for user_data in test_users:
            user, created = CustomUser.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'campus': user_data['campus'],
                    'phone_number': user_data['phone_number'],
                    'student_id': user_data['student_id'],
                    'role': user_data['role'],
                    'is_active': True,
                    'is_email_verified': True
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
            users.append(user)
        
        return users

    def get_category_images(self):
        return {
            'electronics': [
                'media/listing_images/hp pc.jpg',
                'media/listing_images/lenovo pc.jpg',
                'media/listing_images/dell pc.jpg',
                'media/listing_images/galaxy note 9.jpg',
                'media/listing_images/iphone.jpg',
                'media/listing_images/galaxy a20.jpg',
                'media/listing_images/huawei y9.jpg'
            ],
            'clothing': [
                'media/listing_images/couples hoodies.jpg',
                'media/listing_images/couples hoodies (2).jpg',
                'media/listing_images/couples hoodies (3).jpg',
                'media/listing_images/couples hoodies (4).jpg',
                'media/listing_images/dress.jpg',
                'media/listing_images/jacket.jpg',
                'media/listing_images/poloneck.jpg',
                'media/listing_images/woolhat.jpg',
                'media/listing_images/jeans hat.jpg',
                'media/listing_images/top.jpg',
                'media/listing_images/woman shorts.jpg',
                'media/listing_images/skin tight.jpg',
                'media/listing_images/skin tightt.jpg',
                'media/listing_images/tight dress.jpg',
                'media/listing_images/black dress.jpg',
                'media/listing_images/tracksuit.webp',
                'media/listing_images/shirt rose.png',
                'media/listing_images/hoodie all black.png',
                'media/listing_images/black hoodie..monkey.png',
                'media/listing_images/black garment kallos veritas.png',
                'media/listing_images/white garment kallos veritas.png'
            ],
            'accessories': [
                'media/listing_images/handbag.jpg',
                'media/listing_images/handbag (2).jpg',
                'media/listing_images/handbag (3).jpg',
                'media/listing_images/slides.jpg',
                'media/listing_images/sneakers.jpg',
                'media/listing_images/shoes.jpg'
            ],
            'food': [
                'media/listing_images/pizza.jpg',
                'media/listing_images/double pizza.jpg',
                'media/listing_images/kfc.jpg'
            ],
            'services': [
                'media/listing_images/picture framing.jpg'
            ]
        }

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate test data...')
        
        # Create test users
        users = self.create_test_users()
        self.stdout.write(self.style.SUCCESS(f'Created {len(users)} test users'))
        
        # Get category images
        category_images = self.get_category_images()
        
        # Sample product data
        products = [
            {
                'title': 'HP Desktop Computer',
                'description': 'Powerful HP desktop computer, perfect for students. Includes monitor, keyboard, and mouse.',
                'category': 'electronics',
                'price': 450.00,
                'condition': 'good',
                'campus': 'main',
                'tags': 'computer, desktop, hp',
                'location': 'Block A'
            },
            {
                'title': 'Samsung Galaxy Note 9',
                'description': 'Samsung Galaxy Note 9 in excellent condition. Includes original box and accessories.',
                'category': 'electronics',
                'price': 350.00,
                'condition': 'like_new',
                'campus': 'main',
                'tags': 'phone, samsung, galaxy',
                'location': 'Block B'
            },
            {
                'title': 'Couple Hoodies Set',
                'description': 'Matching couple hoodies, perfect for winter. Both size M, barely worn.',
                'category': 'clothing',
                'price': 45.00,
                'condition': 'like_new',
                'campus': 'mashava',
                'tags': 'hoodie, clothing, couple',
                'location': 'Block C'
            },
            {
                'title': 'Designer Handbag Collection',
                'description': 'Set of 3 designer handbags in excellent condition. Selling as a set.',
                'category': 'accessories',
                'price': 120.00,
                'condition': 'good',
                'campus': 'mucheke',
                'tags': 'handbag, accessories, designer',
                'location': 'Block D'
            },
            {
                'title': 'Fresh Pizza Delivery',
                'description': 'Freshly made pizza, available for delivery on campus. Multiple toppings available.',
                'category': 'food',
                'price': 15.00,
                'condition': 'new',
                'campus': 'main',
                'tags': 'food, pizza, delivery',
                'location': 'Cafeteria'
            },
            {
                'title': 'Picture Framing Service',
                'description': 'Professional picture framing service. Various frame styles available.',
                'category': 'services',
                'price': 25.00,
                'condition': 'new',
                'campus': 'main',
                'tags': 'service, framing, pictures',
                'location': 'Arts Center'
            },
            {
                'title': 'Kallos Veritas Garments',
                'description': 'Authentic Kallos Veritas garments in black and white. Perfect condition.',
                'category': 'clothing',
                'price': 85.00,
                'condition': 'new',
                'campus': 'mashava',
                'tags': 'clothing, garments, kallos',
                'location': 'Block E'
            },
            {
                'title': 'Designer Sneakers Collection',
                'description': 'Collection of designer sneakers in various sizes. All in excellent condition.',
                'category': 'accessories',
                'price': 95.00,
                'condition': 'like_new',
                'campus': 'mucheke',
                'tags': 'shoes, sneakers, designer',
                'location': 'Block F'
            }
        ]
        
        # Create listings
        for product in products:
            # Randomly select a user
            owner = random.choice(users)
            
            # Random creation date within last 30 days
            days_ago = random.randint(0, 30)
            created_at = datetime.now() - timedelta(days=days_ago)
            
            # Random status (mostly active, some sold)
            status = 'sold' if random.random() < 0.2 else 'active'
            
            # Random premium status (20% chance)
            premium = random.random() < 0.2
            
            listing = Listing.objects.create(
                owner=owner,
                title=product['title'],
                category=product['category'],
                description=product['description'],
                price=product['price'],
                status=status,
                campus=product['campus'],
                condition=product['condition'],
                tags=product['tags'],
                location=product['location'],
                created_at=created_at,
                premium=premium
            )
            
            # Add images for the category
            images = category_images.get(product['category'], [])
            if images:
                # Select 1-3 random images for this category
                num_images = min(random.randint(1, 3), len(images))
                selected_images = random.sample(images, num_images)
                
                for image_path in selected_images:
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as f:
                            ListingImage.objects.create(
                                listing=listing,
                                image=File(f, name=os.path.basename(image_path))
                            )
            
            self.stdout.write(self.style.SUCCESS(f'Created listing: {listing.title}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully populated test data!')) 