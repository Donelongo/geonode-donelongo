# my_geonode/subscribers/utils.py
from django.core.mail import EmailMessage, EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.conf import settings
from django.urls import reverse

from .models import Subscriber
from info_hub.models import AdvisoryMessage

def send_new_advisory_email(advisory_message_instance):
    active_subscribers = Subscriber.objects.filter(is_active=True)
    if not active_subscribers:
        print("No active subscribers to send email to.")
        return

    subject = f"New Agro-Climate Advisory: {advisory_message_instance.title}"
    from_email = settings.DEFAULT_FROM_EMAIL
    connection = get_connection()
    messages = []

    for subscriber in active_subscribers:
        advisory_url = f"{settings.BASE_URL}/advisory/{advisory_message_instance.id}/"
        pdf_download_url = f"{settings.BASE_URL}/advisory/{advisory_message_instance.id}/pdf/"
        unsubscribe_url = f"{settings.BASE_URL}/api/subscribers/unsubscribe/{subscriber.id}/{subscriber.token}/"

        html_message = render_to_string(
            'emails/new_advisory_email.html',
            {
                'advisory_title': advisory_message_instance.title,
                'advisory_content': advisory_message_instance.advisory_content,
                'suggestion': advisory_message_instance.suggestion,
                'rainfall_forecast': advisory_message_instance.rainfall_forecast,
                'temperature_outlook': advisory_message_instance.temperature_outlook,
                'potential_risks': advisory_message_instance.potential_risks,
                'advisory_url': advisory_url,
                'pdf_download_url': pdf_download_url,
                'unsubscribe_url': unsubscribe_url,
            }
        )

        plain_message = f"""
{advisory_message_instance.title}

{advisory_message_instance.advisory_content}

View advisory: {advisory_url}
Download PDF: {pdf_download_url}
Unsubscribe: {unsubscribe_url}
"""

        msg = EmailMessage(
            subject,
            html_message,
            from_email,
            [subscriber.email],
            connection=connection
        )
        msg.content_subtype = "html"
        msg.alternatives = [(plain_message, "text/plain")]
        messages.append(msg)

    try:
        sent_count = connection.send_messages(messages)
        print(f"✅ Sent {sent_count} advisory emails successfully.")
    except Exception as e:
        print(f"❌ Error sending advisory emails: {e}")


def send_confirmation_email(subscriber):
    subject = "Welcome to Agro Climate Advisory - Subscription Confirmed!"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [subscriber.email]

    unsubscribe_url = f"{settings.BASE_URL}{reverse('subscribers:unsubscribe', args=[subscriber.id, subscriber.token])}"

    try:
        html_content = render_to_string(
            'emails/confirmation_email.html',
            {
                'subscriber_first_name': subscriber.first_name,
                'subscriber_email': subscriber.email,
                'unsubscribe_url': unsubscribe_url,
            }
        )
    except TemplateDoesNotExist as e:
        print(f"Confirmation email template not found: {e}")
        html_content = None

    text_content = (
        f"Dear {subscriber.first_name or 'Subscriber'},\n\n"
        f"Thank you for subscribing to the Agro Climate Advisory System.\n"
        f"You'll now receive updates at {subscriber.email}.\n\n"
        f"If you ever want to unsubscribe, click here:\n{unsubscribe_url}\n\n"
        f"Best regards,\nThe Agro Climate Advisory Team"
    )

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    if html_content:
        msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        print(f"✅ Successfully sent confirmation email to {subscriber.email}")
    except Exception as e:
        print(f"❌ Error sending confirmation email to {subscriber.email}: {e}")
