# src/my_geonode/info_hub/signals.py

print("🐍 signals.py is being imported...")  # <- This must show up in logs

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AdvisoryMessage
from info_hub.tasks import send_new_advisory_email_task

@receiver(post_save, sender=AdvisoryMessage)
def advisory_post_save_handler(sender, instance, created, **kwargs):
    print("🚨 post_save signal triggered")
    if created:
        print(f"✅ Signal caught: {instance.title}")
        try:
            print("📧 Sending advisory email...")
            send_new_advisory_email_task.delay(instance.id)
        except Exception as e:
            print(f"❌ Failed to send email: {e}")

