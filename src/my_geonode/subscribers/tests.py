from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Subscriber


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SubscriptionEmailTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_new_subscription_sends_email(self):
		resp = self.client.post('/api/subscribers/', {
			'email': 'test@example.com',
			'first_name': 'Test',
			'last_name': 'User'
		}, format='json')
		self.assertEqual(resp.status_code, 201, resp.content)
		self.assertTrue(Subscriber.objects.filter(email='test@example.com').exists())
		# locmem backend stores emails in django.core.mail.outbox
		from django.core import mail
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn('Subscription successful', resp.json()['message'])

