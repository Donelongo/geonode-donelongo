from django.apps import AppConfig


class SubscribersConfig(AppConfig):
    name = "subscribers"
    verbose_name = "Subscribers"

    def ready(self):  # pragma: no cover
        # Import signal handlers to guarantee registration
        try:
            import subscribers.signals  # noqa: F401
            print("[SUBSCRIBERS] signals imported")
        except Exception as e:
            print(f"[SUBSCRIBERS] failed importing signals: {e}")
# my_geonode/subscribers/apps.py
from django.apps import AppConfig

class SubscribersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscribers'

    def ready(self):
        import subscribers.signals  # ensures the signal above is triggered
