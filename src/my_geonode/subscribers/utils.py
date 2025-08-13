# my_geonode/subscribers/utils.py
from django.core.mail import EmailMessage, EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.template import TemplateSyntaxError
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

    base = getattr(settings, 'SITEURL', getattr(settings, 'BASE_URL', 'http://localhost:3500/'))
    if not base.endswith('/'):
        base = base + '/'
    advisory_url_base = base + 'advisory'

    for subscriber in active_subscribers:
        advisory_url = advisory_url_base
        # pdf_download_url = f"{settings.BASE_URL}/advisory/{advisory_message_instance.id}/pdf/"
        path_to_pdf = reverse('info_hub:advisory_pdf', kwargs={'advisory_id': advisory_message_instance.id})
        pdf_download_url = f"{settings.BASE_URL}{path_to_pdf}"
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


def send_confirmation_email(subscriber) -> bool:
    """Simpler confirmation email send using EmailMessage like advisory sender."""
    subject = "Welcome to Agro Climate Advisory - Subscription Confirmed!"
    unsubscribe_url = f"{settings.BASE_URL}{reverse('subscribers:unsubscribe', args=[subscriber.id, subscriber.token])}"
    explore_url = f"{getattr(settings,'SITEURL', settings.BASE_URL)}advisory"
    support_url = f"{getattr(settings,'SITEURL', settings.BASE_URL)}contact"
    print(f"[CONFIRMATION] START subscriber={subscriber.email} backend={settings.EMAIL_BACKEND}", flush=True)
    # Extra diagnostics (mask password) to understand why email might not send
    try:
        masked_user = (settings.EMAIL_HOST_USER[:2] + "***" + settings.EMAIL_HOST_USER[-2:]) if getattr(settings, 'EMAIL_HOST_USER', None) else None
        print(
            f"[CONFIRMATION][DEBUG] host={getattr(settings,'EMAIL_HOST',None)} port={getattr(settings,'EMAIL_PORT',None)} tls={getattr(settings,'EMAIL_USE_TLS',None)} ssl={getattr(settings,'EMAIL_USE_SSL',None)} user={masked_user}",
            flush=True,
        )
    except Exception as diag_e:
        print(f"[CONFIRMATION][DEBUG] unable to print SMTP diagnostics: {diag_e}", flush=True)
    try:
        html_body = render_to_string('emails/confirmation_email.html', {
            'subscriber_first_name': subscriber.first_name,
            'subscriber_email': subscriber.email,
            'unsubscribe_url': unsubscribe_url,
            'explore_url': explore_url,
            'support_url': support_url,
        })
    except (TemplateDoesNotExist, TemplateSyntaxError) as tmpl_err:
        print(f"[CONFIRMATION][TEMPLATE_FALLBACK] {tmpl_err}", flush=True)
        html_body = None
    if not html_body:
        html_body = f"<p>Welcome {subscriber.first_name or 'Subscriber'}!</p><p>Explore: {explore_url}</p><p>Unsubscribe: {unsubscribe_url}</p>"
    backend = get_connection()
    try:
        # If it's SMTPBackend, open early to capture connection errors explicitly
        backend.open()
        print(f"[CONFIRMATION][DEBUG] connection opened successfully", flush=True)
    except Exception as open_err:
        print(f"[CONFIRMATION][ERROR] opening connection failed: {open_err}", flush=True)
    msg = EmailMessage(subject=subject,
                       body=html_body,
                       from_email=settings.DEFAULT_FROM_EMAIL or 'no-reply@localhost',
                       to=[subscriber.email],
                       connection=backend)
    msg.content_subtype = 'html'
    try:
        sent = msg.send(fail_silently=False)
        print(f"[CONFIRMATION] SENT={sent} subscriber={subscriber.email}", flush=True)
        if sent:
            return True
    except Exception as e:
        print(f"[CONFIRMATION] ERROR subscriber={subscriber.email} err={e}", flush=True)
    # fallback console
    if settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend':
        try:
            console_conn = get_connection('django.core.mail.backends.console.EmailBackend')
            msg.connection = console_conn
            msg.send(fail_silently=True)
            print(f"[CONFIRMATION] FALLBACK_CONSOLE subscriber={subscriber.email}", flush=True)
        except Exception as ee:
            print(f"[CONFIRMATION] FALLBACK_FAIL subscriber={subscriber.email} err={ee}", flush=True)
    return False



def send_unsubscribe_confirmation_email(subscriber):
    subject = "You have unsubscribed from Agro Climate Advisory"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [subscriber.email]
    # Offer a path back if user changes mind later
    explore_url = f"{getattr(settings,'SITEURL', settings.BASE_URL)}advisory"

    try:
        html_content = render_to_string(
            'emails/unsubscribe_confirmation.html',
            {
                'subscriber_first_name': subscriber.first_name,
                'subscriber_email': subscriber.email,
                'explore_url': explore_url,
            }
        )
    except TemplateDoesNotExist as e:
        print(f"Unsubscribe confirmation email template not found: {e}")
        html_content = None

    text_content = (
        f"Dear {subscriber.first_name or 'Subscriber'},\n\n"
        f"You have successfully unsubscribed from the Agro Climate Advisory System.\n"
        f"You will no longer receive updates at {subscriber.email}.\n\n"
        f"Best regards,\nThe Agro Climate Advisory Team"
    )

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    if html_content:
        msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        print(f"✅ Successfully sent unsubscribe confirmation email to {subscriber.email}")
    except Exception as e:
        print(f"❌ Error sending unsubscribe confirmation email to {subscriber.email}: {e}")
