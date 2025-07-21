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
        instance = self.instance # Get the instance if this is an update

        if instance and instance.email == value: # If email hasn't changed on update
            return value

        # For new instances or if email changed on update, check for existing active subscribers
        if Subscriber.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("Subscriber with this email is already active.")

        return value

    # The update method is implicitly handled by ModelSerializer,
    # but you could customize it if needed.
    # However, for simply setting is_active=True, the view's save(is_active=True) is correct.