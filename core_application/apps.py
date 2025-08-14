from django.apps import AppConfig


class CoreApplicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core_application'

    def ready(self):
        import core_application.signals  
