from celery import shared_task
from info_hub.models import AdvisoryMessage
from .utils import send_new_advisory_email

@shared_task
def send_new_advisory_email_task(advisory_id):
    advisory = AdvisoryMessage.objects.get(id=advisory_id)
    send_new_advisory_email(advisory)
