from rest_framework import status, viewsets
from rest_framework.response import Response
from .models import Subscriber
from .serializers import SubscriberSerializer
from .utils import send_confirmation_email
import json
from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    list=extend_schema(summary="List subscribers"),
    create=extend_schema(summary="Create subscriber"),
)

class SubscriberViewSet(viewsets.ModelViewSet):
    queryset = Subscriber.objects.all()
    serializer_class = SubscriberSerializer

    def create(self, request, *args, **kwargs):
        print("\n--- Incoming Request Debug ---")
        print(f"Request Method: {request.method}")
        print(f"Request Headers: {request.headers}")
        print(f"Request Content-Type: {request.headers.get('Content-Type')}")

        try:
            print(f"Request Raw Body: {request.body.decode('utf-8')}")
        except Exception as e:
            print(f"Error decoding request.body: {e}")

        try:
            print(f"Request Parsed Data (request.data): {request.data}")
        except Exception as e:
            print(f"Error parsing request.data: {e}")
        print("--- End Request Debug ---\n")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')

        try:
            subscriber = Subscriber.objects.get(email=email)
            update_serializer = self.get_serializer(subscriber, data=request.data, partial=True)
            update_serializer.is_valid(raise_exception=True)

            if not subscriber.is_active:
                subscriber = update_serializer.save(is_active=True)
                send_confirmation_email(subscriber)
                return Response(
                    {"message": "Email reactivated successfully and confirmation sent."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "This email is already subscribed and active."},
                    status=status.HTTP_409_CONFLICT
                )
        except Subscriber.DoesNotExist:
            subscriber = serializer.save()
            send_confirmation_email(subscriber)
            headers = self.get_success_headers(serializer.data)
            return Response(
                {"message": "Subscription successful! Confirmation email sent."},
                status=status.HTTP_201_CREATED,
                headers=headers
            )

# Unsubscribe view remains unchanged
from django.shortcuts import render, get_object_or_404

def unsubscribe_view(request, subscriber_id, token):
    try:
        subscriber = get_object_or_404(Subscriber, pk=subscriber_id)

        if subscriber.token == token and subscriber.is_active:
            subscriber.is_active = False
            subscriber.save(update_fields=['is_active'])
            message = "You have been successfully unsubscribed."
            status_code = 200
        elif not subscriber.is_active:
            message = "You are already unsubscribed."
            status_code = 200
        else:
            message = "Invalid unsubscribe link or token."
            status_code = 400
    except Subscriber.DoesNotExist:
        message = "Subscriber not found or invalid link."
        status_code = 404
    except Exception as e:
        message = f"An error occurred during unsubscription: {e}"
        status_code = 500

    return render(request, 'emails/unsubscribe_confirmation.html', {
        'message': message,
        'status': status_code
    }, status=status_code)
