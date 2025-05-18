from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

# Create your tests here.

class MessagingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_inbox_view_requires_login(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('inbox'))
        self.assertEqual(response.status_code, 200)
