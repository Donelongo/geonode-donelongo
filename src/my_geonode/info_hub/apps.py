# info_hub/apps.py
from django.apps import AppConfig

class InfoHubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'info_hub'

    def ready(self):
        print("🧠 InfoHubConfig.ready() called")  # ← Should appear in logs
        import info_hub.signals  # noqa
        # Ensure modeltranslation registration happens on app ready
        # try:
        #     import info_hub.translation  # noqa
        # except Exception:
        #     # Avoid breaking startup if modeltranslation isn't installed yet
        #     pass
