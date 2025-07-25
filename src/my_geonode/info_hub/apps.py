# info_hub/apps.py
from django.apps import AppConfig

class InfoHubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'info_hub'
    def ready(self):
        import info_hub.signals  # noqa: F401