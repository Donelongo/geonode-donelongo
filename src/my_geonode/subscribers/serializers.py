# subscribers/serializers.py
from rest_framework import serializers
from .models import Subscriber

class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = ['first_name', 'last_name', 'email', 'is_active'] # Include 'is_active' here so it can be updated
        read_only_fields = ['subscribed_at'] # 'is_active' is no longer read-only

        # Add this to ensure unique email validation happens ONLY on creation
        # This is often default but explicit makes it clear
        extra_kwargs = {
            'email': {'validators': []}, # Remove default unique validator
        }

    # Custom validation to handle unique email check for existing active users
    def validate_email(self, value):
        """
        Allow passing an email that might already exist so the ViewSet logic can
        decide whether to reactivate (200) or return a 409 conflict. We only
        enforce format-level validation here; uniqueness is handled at the
        application layer.
        """
        return value

    # The update method is implicitly handled by ModelSerializer,
    # but you could customize it if needed.
    # However, for simply setting is_active=True, the view's save(is_active=True) is correct.