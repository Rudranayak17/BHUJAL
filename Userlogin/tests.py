from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Profile


class SignupTests(TestCase):
    def setUp(self):
        self.url = reverse('Signup')
        self.payload = {
            'username': 'rudra',
            'email': 'newuser@example.com',
            'password': 'StrongPass123',
            'password2': 'StrongPass123',
            'role': 'FARMER',
            'state': 'Andhra Pradesh',
            'district': 'Anantapur',
        }

    def test_duplicate_username_shows_error_instead_of_crashing(self):
        User.objects.create_user(
            username='rudra',
            email='existing@example.com',
            password='ExistingPass123',
        )

        response = self.client.post(self.url, self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Username already taken')
        self.assertEqual(User.objects.filter(username__iexact='rudra').count(), 1)

    def test_duplicate_username_is_case_insensitive(self):
        User.objects.create_user(
            username='Rudra',
            email='existing@example.com',
            password='ExistingPass123',
        )

        response = self.client.post(self.url, self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Username already taken')
        self.assertEqual(User.objects.filter(username__iexact='rudra').count(), 1)

    def test_successful_signup_creates_user_and_profile(self):
        response = self.client.post(self.url, self.payload)

        self.assertRedirects(response, reverse('Login'))
        user = User.objects.get(username='rudra')
        self.assertTrue(Profile.objects.filter(user=user, role='FARMER').exists())
