from django.apps import AppConfig
from allauth.account.signals import user_logged_in
from allauth.account.signals import user_signed_up
from django.conf import settings

class NucleoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nucleo'

    # def ready(self): ## Registro de señales para detectar eventos del sistema
    #     from . import nucleo_signals
    #     user_logged_in.connect(receiver=nucleo_signals.users_creation_handler,
    #                            sender='nucleo.Users',
    #                            dispatch_uid=settings.SIGNAL_KEY_USER_CREATE)
