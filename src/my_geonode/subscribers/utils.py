# agro_advisory_system/subscribers/utils.py
from django.core.mail import send_mass_mail, EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse # NEW: Import reverse for URL generation
from .models import Subscriber
from info_hub.models import AdvisoryMessage

def send_new_advisory_email(advisory_message_instance):
    """
    Sends an email to all active subscribers with details about a new advisory.
    """
    active_subscribers = Subscriber.objects.filter(is_active=True)

    if not active_subscribers:
        print("No active subscribers to send email to.")
        return

    subject = f"New Agro-Climate Advisory: {advisory_message_instance.title}"
    from_email = settings.DEFAULT_FROM_EMAIL

    messages = []
    # Loop through each active subscriber to generate unique links
    for subscriber in active_subscribers:
        # Construct the PDF download URL (already in place)
        path_to_pdf_download = reverse('info_hub:download_advisory_pdf', kwargs={'advisory_id': advisory_message_instance.id})
        # IMPORTANT: Replace "http://172.29.29.48:9000" with your actual Django backend's base URL (IP/Port)
        # In production, this should be your domain (e.g., "https://yourdomain.com")
        base_url_backend = "http://172.29.29.191:9000"
        pdf_download_url = f"{base_url_backend}{path_to_pdf_download}"

        # --- NEW: Construct the Unsubscribe URL ---
        # Use the 'subscribers' app_name and the 'unsubscribe' URL name
        # Pass subscriber.id and subscriber.token as keyword arguments
        path_to_unsubscribe = reverse(
            'subscribers:unsubscribe',
            kwargs={'subscriber_id': subscriber.id, 'token': subscriber.token}
        )
        # Use the same base URL as your backend for the unsubscribe link
        unsubscribe_url = f"{base_url_backend}{path_to_unsubscribe}"

        # Render the HTML part of the email
        html_message = render_to_string(
            'emails/new_advisory_email.html',
            {
                'advisory_title': advisory_message_instance.title,
                'advisory_content': advisory_message_instance.advisory_content,
                # Assuming your frontend is at localhost:3000
                'advisory_url': f"http://localhost:3000/advisories/{advisory_message_instance.id}/",
                'pdf_download_url': pdf_download_url,
                'unsubscribe_url': unsubscribe_url, # <-- Pass the dynamic unsubscribe URL
            }
        )

        # Render the plain text part of the email
        plain_message = f"""
Dear Subscriber,

A new Agro-Climate Advisory has been posted:

Title: {advisory_message_instance.title}
Content: {advisory_message_instance.advisory_content}

Download this advisory as PDF: {pdf_download_url}

Read more here: http://localhost:3000/advisories/{advisory_message_instance.id}/

To unsubscribe from these emails, visit: {unsubscribe_url}

Best regards,
Your Agro Advisory Team
        """

        msg = EmailMessage(
            subject,
            html_message, # Use HTML content
            from_email,
            [subscriber.email] # Send to the current subscriber's email
        )
        msg.content_subtype = "html" # Specify content as HTML
        msg.alternatives = [(plain_message, "text/plain")] # Add plain text alternative
        messages.append(msg)

    try:
        # Instead of send_mass_mail, iterate and send individual messages
        # This is more robust for debugging and unique per-subscriber content (like unsubscribe links)
        for msg in messages:
            msg.send(fail_silently=False)
        print(f"Successfully sent new advisory email to {len(active_subscribers)} subscribers.")
    except Exception as e:
        print(f"Error sending advisory emails: {e}")

# Keep your send_confirmation_email function as is (unless you want to add unsubscribe to it too)
def send_confirmation_email(subscriber):
    subject = "Welcome to Agro Climate Advisory - Subscription Confirmed!"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [subscriber.email]

    html_content = render_to_string(
        'emails/confirmation_email.html',
        {
            'subscriber_first_name': subscriber.first_name,
            'subscriber_email': subscriber.email,
        }
    )
    text_content = (
        f"Dear {subscriber.first_name or 'Subscriber'},\n\n"
        f"We're thrilled to confirm your subscription to the Agro Climate Advisory System.\n\n"
        f"You'll now receive timely updates and important advisories directly to your inbox at {subscriber.email}.\n\n"
        f"Best regards,\n"
        f"The Agro Climate Advisory Team"
    )

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    try:
        msg.send(fail_silently=False)
        print(f"Successfully sent confirmation email to {subscriber.email}")
    except Exception as e:
        print(f"Error sending confirmation email to {subscriber.email}: {e}")