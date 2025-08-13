from celery import shared_task
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, get_connection
from .models import Subscriber

@shared_task
def send_welcome_email_task(subscriber_id):
    try:
        subscriber = Subscriber.objects.get(id=subscriber_id)
        subject = "🌱 Welcome to the Agro-Climate Advisory Service"

        html_message = render_to_string("emails/confirmation_email.html", {
                    "subscriber_first_name": subscriber.first_name,
                    "subscriber_email": subscriber.email,
                    "explore_url": "{0}advisory".format(getattr(__import__('django.conf').conf.settings,'SITEURL','/')),
                    "support_url": "{0}contact".format(getattr(__import__('django.conf').conf.settings,'SITEURL','/')),
                })

        plain_message = f"Welcome, {subscriber.email}!\n\nThank you for subscribing."

        connection = get_connection()
        msg = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL
            to=[subscriber.email],
            connection=connection,
        )
        msg.content_subtype = "html"
        msg.send()
        print(f"✅ Sent welcome email to {subscriber.email}")
    except Exception as e:
        print(f"❌ Failed to send welcome email: {e}")
