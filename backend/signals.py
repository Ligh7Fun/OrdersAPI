from django.dispatch import Signal, receiver
from django.core.mail import EmailMultiAlternatives
from backend.models import ConfirmEmailToken, User
from django.db.models.signals import post_save
from django.conf import settings
from typing import Type

# new_user_registered = Signal()


@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User, created: bool, **kwargs):
    print('[Signal] New user registered:', instance.pk)
    if not instance.is_active:
        token, _ = ConfirmEmailToken.objects.get_or_create(user_id=instance.pk)
        print(f'Для подтверждения регистрации перейдите по ссылке: http://127.0.0.1:8000/api/user/register/confirm/?token={token.key}&email={instance.email}')

        #
        # message = EmailMultiAlternatives(
        #     # title:
        #     'Подтверждение регистрации',
        #     # message:
        #     f'Для подтверждения регистрации перейдите по ссылке: http://127.0.0.1:8000/api/user/register/confirm/?token={token.key}&email={instance.email}',
        #     # from:
        #     settings.EMAIL_HOST_USER,
        #     # to:
        #     [instance.email]
        # )
        # message.send()
