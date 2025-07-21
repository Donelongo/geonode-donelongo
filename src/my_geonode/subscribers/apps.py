# agro_advisory_system/subscribers/apps.py
from django.apps import AppConfig

class SubscribersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscribers'

    def ready(self):
        # Import signals so they are registered with Django
        import subscribers.signals # This line registers the signals