from rest_framework import status, viewsets
import logging
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import Subscriber
from .serializers import SubscriberSerializer
from .utils import send_confirmation_email, send_unsubscribe_confirmation_email
import secrets
import threading
from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    list=extend_schema(summary="List subscribers"),
    create=extend_schema(summary="Create subscriber"),
)


@method_decorator(csrf_exempt, name="dispatch")
class SubscriberViewSet(viewsets.ModelViewSet):
    logger = logging.getLogger("subscribers")
    queryset = Subscriber.objects.all()
    serializer_class = SubscriberSerializer
    # Open endpoint: no auth required, avoid SessionAuthentication CSRF enforcement
    authentication_classes: list = []  # type: ignore
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        print("\n--- Incoming Request Debug ---", flush=True)
        print(f"Request Method: {request.method}", flush=True)
        print(f"Request Headers: {request.headers}", flush=True)
        print(f"Request Content-Type: {request.headers.get('Content-Type')}", flush=True)

        try:
            print(f"Request Raw Body: {request.body.decode('utf-8')}", flush=True)
        except Exception as e:
            print(f"Error decoding request.body: {e}", flush=True)

        try:
            print(f"Request Parsed Data (request.data): {request.data}", flush=True)
        except Exception as e:
            print(f"Error parsing request.data: {e}", flush=True)
        print("--- End Request Debug ---\n", flush=True)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        def _async(fn, *args, **kwargs):
            try:
                threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True).start()
            except Exception:
                pass  # Fail silently; logging could be added

        try:
            subscriber = Subscriber.objects.get(email=email)
            update_serializer = self.get_serializer(subscriber, data=request.data, partial=True)
            update_serializer.is_valid(raise_exception=True)

            if not subscriber.is_active:
                subscriber = update_serializer.save(is_active=True)
                if not subscriber.token:
                    subscriber.token = secrets.token_urlsafe(32)
                    subscriber.save(update_fields=["token"])
                print(f"[VIEW] Reactivation path for {subscriber.email}", flush=True)
                self.logger.info("Reactivation path for %s", subscriber.email)
                success = False
                try:
                    success = send_confirmation_email(subscriber)
                except Exception as mail_err:
                    print(f"[VIEW] Reactivation exception {mail_err}", flush=True)
                    print(f"[VIEW] Reactivation send result success={success}", flush=True)
                    self.logger.exception("Reactivation email exception for %s", subscriber.email)
                self.logger.info("Reactivation send result success=%s email=%s", success, subscriber.email)
                status_msg = "Email reactivated. Confirmation email sent." if success else "Email reactivated (email delivery issue logged)."
                return Response({"message": status_msg}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "This email is already subscribed and active."}, status=status.HTTP_409_CONFLICT)
        except Subscriber.DoesNotExist:
            subscriber = serializer.save()
            if not subscriber.token:
                subscriber.token = secrets.token_urlsafe(32)
                subscriber.save(update_fields=["token"])
            print(f"[VIEW] New subscription path for {subscriber.email}", flush=True)
            self.logger.info("New subscription path for %s", subscriber.email)
            success = False
            try:
                success = send_confirmation_email(subscriber)
            except Exception as mail_err:
                print(f"[VIEW] New subscription exception {mail_err}", flush=True)
                self.logger.exception("New subscription email exception for %s", subscriber.email)
            print(f"[VIEW] New subscription send result success={success}", flush=True)
            self.logger.info("New subscription send result success=%s email=%s", success, subscriber.email)
            msg_txt = "Subscription successful! Confirmation email sent." if success else "Subscription successful (email delivery issue logged)."
            headers = self.get_success_headers(serializer.data)
            return Response({"message": msg_txt}, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            return Response({"detail": f"Unexpected error processing request: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Unsubscribe view remains unchanged
from django.shortcuts import render, get_object_or_404


def unsubscribe_view(request, subscriber_id, token):
    try:
        subscriber = get_object_or_404(Subscriber, pk=subscriber_id)

        if subscriber.token == token and subscriber.is_active:
            # Deactivate the subscriber
            subscriber.is_active = False
            subscriber.save(update_fields=['is_active'])

            # Send the detailed, email-compatible confirmation email
            # This function (in .utils) will use 'emails/unsubscribe_success_email_template.html'
            send_unsubscribe_confirmation_email(subscriber)

            # Render the simplified web confirmation page immediately
            # This is 'emails/unsubscribe_web_confirmation.html'
            return render(request, 'emails/unsubscribe_web_confirmation.html')

        elif not subscriber.is_active:
            # If the subscriber is already inactive, still show the success web page
            # and optionally send a specific "already unsubscribed" email if needed.
            return render(request, 'emails/unsubscribe_web_confirmation.html')
        else:
            # Case for invalid token or mismatch
            message = "The unsubscribe link is invalid or has expired."
            status_code = 400
            # Render the web error page
            return render(request, 'emails/unsubscribe_error_web.html', {
                'message': message
            }, status=status_code)

    except Subscriber.DoesNotExist:
        message = "Subscriber not found or invalid link."
        status_code = 404
        # Render the web error page
        return render(request, 'emails/unsubscribe_error_web.html', {
            'message': message
        }, status=status_code)
    except Exception as e:
        # Catch any other unexpected errors
        message = f"An unexpected error occurred: {e}"
        status_code = 500
        # Render the web error page
        return render(request, 'emails/unsubscribe_error_web.html', {
            'message': message
        }, status=status_code)

