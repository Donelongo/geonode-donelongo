# my_geonode/subscribers/signals.py
import secrets
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Subscriber
from info_hub.models import AdvisoryMessage  # noqa: F401 (may be used later)
from .utils import send_confirmation_email


@receiver(pre_save, sender=Subscriber)
def generate_subscriber_token(sender, instance, **kwargs):
    if not instance.token:
        instance.token = secrets.token_urlsafe(32)


@receiver(post_save, sender=Subscriber)
def send_confirmation_on_create(sender, instance, created, **kwargs):
    """Always send confirmation email on first creation.

    Temporarily restored to guarantee email delivery while view logic
    is being iterated. Avoids dependency on custom flags. If duplicate
    mails ever appear, we can re-introduce gating once the view code is
    confirmed deployed in the container.
    """
    if created:
        print(f"[SIGNAL_CONFIRM] New subscriber {instance.email} -> sending confirmation email (signal)")
        try:
            ok = send_confirmation_email(instance)
            print(f"[SIGNAL_CONFIRM] Result for {instance.email}: {ok}")
        except Exception as e:
            print(f"[SIGNAL_CONFIRM] ERROR sending confirmation for {instance.email}: {e}")
