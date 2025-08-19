# Edit contact/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import ContactMessage
from .serializers import ContactMessageSerializer

@method_decorator(csrf_exempt, name='dispatch')
class ContactMessageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Simple health check to debug 502 issues."""
        return Response({"status": "ok", "detail": "contact endpoint ready"})

    def post(self, request, *args, **kwargs):
        serializer = ContactMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            contact_message = serializer.save()
        except Exception as db_exc:
            # Common root cause: missing migrations / table does not exist
            return Response({
                "message": "Failed to save contact message.",
                "error": str(db_exc),
                "hint": "Run migrations inside the django container: manage.py makemigrations contact && manage.py migrate"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Attempt email notification if configuration present
        admin_email = getattr(settings, 'ADMIN_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if admin_email:
            try:
                subject = "New Contact Form Message"
                message_body = (
                    "You have received a new message from your website's contact form.\n\n"
                    f"From: {contact_message.first_name} {contact_message.last_name}\n"
                    f"Email: {contact_message.email}\n"
                    f"Phone: {contact_message.phone_number if contact_message.phone_number else 'N/A'}\n\n"
                    f"Message:\n{contact_message.message}\n"
                )
                send_mail(
                    subject=subject,
                    message=message_body,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', admin_email),
                    recipient_list=[admin_email],
                    fail_silently=True,
                )
            except Exception as e:  # pragma: no cover - logging only
                print(f"Error sending contact form email notification: {e}")

        return Response({
            "message": "Thank you! Your message has been sent successfully.",
            "data": {
                "first_name": contact_message.first_name,
                "last_name": contact_message.last_name,
                "email": contact_message.email,
                "phone_number": contact_message.phone_number,
                "id": contact_message.id,
            }
        }, status=status.HTTP_201_CREATED)