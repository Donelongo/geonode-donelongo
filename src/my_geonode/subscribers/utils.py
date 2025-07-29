# my_geonode/subscribers/utils.py
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.conf import settings
from django.urls import reverse
from django.core.mail import get_connection


from .models import Subscriber
from info_hub.models import AdvisoryMessage

def send_new_advisory_email(advisory_message_instance):
    active_subscribers = Subscriber.objects.filter(is_active=True)
    if not active_subscribers:
        print("No active subscribers to send email to.")
        return

    subject = f"New Agro-Climate Advisory: {advisory_message_instance.title}"
    from_email = settings.DEFAULT_FROM_EMAIL

    connection = get_connection()  # 🔄 Reuse SMTP connection
    messages = []

    for subscriber in active_subscribers:
        # Email content
        html_message = f"""
        <html>
            <body>
                <h2>{advisory_message_instance.title}</h2>
                <p>{advisory_message_instance.advisory_content}</p>
                <p><a href="http://example.com/advisory/{advisory_message_instance.id}/">View full advisory</a></p>
            </body>
        </html>
        """
        plain_message = f"""
        Title: {advisory_message_instance.title}
        Message: {advisory_message_instance.advisory_content}
        View the full advisory: http://example.com/advisory/{advisory_message_instance.id}/
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
        sent_count = connection.send_messages(messages)  # 📤 Send all at once
        print(f"✅ Sent {sent_count} advisory emails successfully.")
    except Exception as e:
        print(f"❌ Error sending advisory emails: {e}")


# Keep your send_confirmation_email function as is (unless you want to add unsubscribe to it too)
def send_confirmation_email(subscriber):
    subject = "Welcome to Agro Climate Advisory - Subscription Confirmed!"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [subscriber.email]

    try:
        html_content = render_to_string(
            'emails/confirmation_email.html',
            {
                'subscriber_first_name': subscriber.first_name,
                'subscriber_email': subscriber.email,
            }
        )
    except TemplateDoesNotExist as e:
        print(f"Confirmation email template not found: {e}")
        html_content = None  # Fallback to plain text only

    text_content = (
        f"Dear {subscriber.first_name or 'Subscriber'},\n\n"
        f"We're thrilled to confirm your subscription to the Agro Climate Advisory System.\n\n"
        f"You'll now receive timely updates and important advisories directly to your inbox at {subscriber.email}.\n\n"
        f"Best regards,\n"
        f"The Agro Climate Advisory Team"
    )

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    if html_content:
        msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        print(f"Successfully sent confirmation email to {subscriber.email}")
    except Exception as e:
        print(f"Error sending confirmation email to {subscriber.email}: {e}")
