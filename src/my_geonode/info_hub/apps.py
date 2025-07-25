# info_hub/apps.py
from django.apps import AppConfig

class InfoHubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'info_hub'

    def ready(self):
        print("🧠 InfoHubConfig.ready() called")  # ← Should appear in logs
        import info_hub.signals  # noqa
