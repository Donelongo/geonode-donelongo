from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from subscribers.models import Subscriber
from subscribers.utils import send_confirmation_email


class Command(BaseCommand):
    help = "Send a test subscription confirmation email to an existing subscriber (or the most recent one)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email", "-e", dest="email", help="Target subscriber email; if omitted uses latest subscriber"
        )

    def handle(self, *args, **options):
        email = options.get("email")
        try:
            if email:
                try:
                    sub = Subscriber.objects.get(email=email)
                except Subscriber.DoesNotExist:
                    raise CommandError(f"Subscriber with email {email} not found")
            else:
                sub = Subscriber.objects.order_by('-subscribed_at').first()
                if not sub:
                    raise CommandError("No subscribers found to test with; create one first.")
            self.stdout.write(self.style.NOTICE("--- SMTP Debug Context ---"))
            for k in [
                'EMAIL_BACKEND','EMAIL_HOST','EMAIL_PORT','EMAIL_USE_TLS','EMAIL_USE_SSL',
                'DEFAULT_FROM_EMAIL','EMAIL_HOST_USER'
            ]:
                self.stdout.write(f"{k}={getattr(settings,k,None)}")
            masked_pw = None
            if getattr(settings, 'EMAIL_HOST_PASSWORD', None):
                pw = settings.EMAIL_HOST_PASSWORD
                masked_pw = pw[:2] + '***' + pw[-2:] if len(pw) > 4 else '***'
            self.stdout.write(f"EMAIL_HOST_PASSWORD(masked)={masked_pw}")
            self.stdout.write(self.style.NOTICE(f"Sending confirmation email to {sub.email}"))
            ok = send_confirmation_email(sub)
            if ok:
                self.stdout.write(self.style.SUCCESS("Email send reported success (sent>0)."))
            else:
                self.stdout.write(self.style.WARNING("Email send returned False (see logs above for ERROR/FALLBACK lines)."))
        except CommandError:
            raise
        except Exception as e:
            raise CommandError(f"Unexpected error: {e}")
