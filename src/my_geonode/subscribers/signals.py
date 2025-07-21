# agro_advisory_system/subscribers/signals.py
import secrets # Used to generate secure random strings
from django.db.models.signals import pre_save # Signal to act before an object is saved
from django.dispatch import receiver # Decorator to connect functions to signals
from .models import Subscriber # Import your Subscriber model

@receiver(pre_save, sender=Subscriber)
def generate_subscriber_token(sender, instance, **kwargs):
    """
    Generates a unique token for a Subscriber before it is saved, if one doesn't already exist.
    """
    if not instance.token: # Only generate if the token field is empty
        instance.token = secrets.token_urlsafe(32) # Generates a URL-safe text string of 32 bytes (around 43 chars)