# my_geonode/subscribers/signals.py
import secrets
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Subscriber
from info_hub.models import AdvisoryMessage
from info_hub.tasks import send_new_advisory_email_task


@receiver(pre_save, sender=Subscriber)
def generate_subscriber_token(sender, instance, **kwargs):
    if not instance.token:
        instance.token = secrets.token_urlsafe(32)


@receiver(post_save, sender=Subscriber)
def send_latest_advisory_to_new_subscriber(sender, instance, created, **kwargs):
    if created:
        print(f"📥 New subscriber registered: {instance.email}")
        advisory = AdvisoryMessage.objects.last()
        if advisory:
            print(f"📤 Sending latest advisory ({advisory.id}) to new subscriber...")
            try:
                send_new_advisory_email_task.delay(advisory.id)
            except Exception as e:
                print(f"❌ Failed to send advisory: {e}")
        else:
            print("⚠️ No advisory found to send.")
