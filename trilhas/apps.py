from django.apps import AppConfig


class TrilhasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trilhas'

    def ready(self):
        from . import signals  # noqa: F401
