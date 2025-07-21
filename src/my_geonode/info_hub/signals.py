# agro_advisory_system/info_hub/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AdvisoryMessage # Ensure AdvisoryMessage is imported
from subscribers.utils import send_new_advisory_email # Ensure email utility is imported

@receiver(post_save, sender=AdvisoryMessage)
def advisory_post_save_handler(sender, instance, created, **kwargs):
    """
    Signal receiver to send email when a new AdvisoryMessage is created.
    """
    if created: # Only send email when a new advisory is created, not on updates
        print(f"Signal caught: New Advisory '{instance.title}' created. Preparing email.")
        # CRUCIAL CHANGE: Pass the full AdvisoryMessage instance to the utility function
        # This matches the signature of send_new_advisory_email in subscribers/utils.py
        send_new_advisory_email(advisory_message_instance=instance)
    else:
        print(f"Advisory '{instance.title}' updated. No email sent (only on creation).")