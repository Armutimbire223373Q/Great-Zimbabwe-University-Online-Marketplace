from django.test import TestCase
from django.urls import reverse

# Create your tests here.

class MarketplaceTests(TestCase):
    def test_listings_view_loads(self):
        response = self.client.get(reverse('listings'))
        self.assertEqual(response.status_code, 200)
