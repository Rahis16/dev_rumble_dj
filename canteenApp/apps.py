from django.apps import AppConfig


class CanteenappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'canteenApp'
    
    def ready(self):
        import canteenApp.signals



