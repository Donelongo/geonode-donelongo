# agro_advisory_system/subscribers/models.py
from django.db import models
# No need for 'uuid' here yet, it was a thought from my side, 'secrets' is used in signal

class Subscriber(models.Model):
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True) # Email must be unique for each subscriber
    subscribed_at = models.DateTimeField(auto_now_add=True) # Automatically set when subscriber is created
    is_active = models.BooleanField(default=True) # To allow deactivating subscriptions
    # NEW FIELD: Unique token for unsubscribe links
    token = models.CharField(max_length=100, unique=True, null=True, blank=True)


    class Meta:
        app_label = 'subscribers'
        verbose_name = "Subscriber"
        verbose_name_plural = "Subscribers"
        ordering = ['-subscribed_at'] # Order by most recent subscriptions first

    def __str__(self):
        return self.email