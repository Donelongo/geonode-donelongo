# src/my_geonode/info_hub/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AdvisoryMessage
from subscribers.utils import send_new_advisory_email

@receiver(post_save, sender=AdvisoryMessage)
def advisory_post_save_handler(sender, instance, created, **kwargs):
    if created:
        print(f"✅ Signal caught for advisory: {instance.title}")
        try:
            print("📧 Calling send_new_advisory_email...")
            send_new_advisory_email(advisory_message_instance=instance)
            print("✅ Email function completed (no exception).")
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
    else:
        print(f"ℹ️ Advisory '{instance.title}' updated. No email sent.")
