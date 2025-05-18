from django.test import TestCase, Client
from django.urls import reverse

# Create your tests here.

class AccountsTests(TestCase):
    def test_register_view_loads(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
