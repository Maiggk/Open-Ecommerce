# from django.db.models.signals import create_user_profile
from django.dispatch import receiver
from django.contrib.auth.models import User
from allauth.account.signals import user_signed_up, user_logged_in


@receiver(user_logged_in, sender=User)
def users_creation_handler(sender,request,user,**kwargs):
    print("<----- Aranda's Creation Users Logic Here ----->:", user.email,
          user.first_name, user.last_name, user.username)
    pass