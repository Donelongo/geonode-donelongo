# Edit contact/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings
from .models import ContactMessage
from .serializers import ContactMessageSerializer

class ContactMessageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            contact_message = serializer.save()

            try:
                # --- Send an email notification to the admin ---
                subject = "New Contact Form Message"
                message_body = f"""
You have received a new message from your website's contact form.

From: {contact_message.first_name} {contact_message.last_name}
Email: {contact_message.email}
Phone: {contact_message.phone_number if contact_message.phone_number else 'N/A'}

Message:
{contact_message.message}
                """
                send_mail(
                    subject=subject,
                    message=message_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending contact form email notification: {e}")

            return Response({"message": "Thank you! Your message has been sent successfully."}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)