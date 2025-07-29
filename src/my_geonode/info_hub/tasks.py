# info_hub/tasks.py

from celery import shared_task
from .models import AdvisoryMessage
from subscribers.utils import send_new_advisory_email

@shared_task
def send_new_advisory_email_task(advisory_id):
    advisory = AdvisoryMessage.objects.get(id=advisory_id)
    send_new_advisory_email(advisory)
