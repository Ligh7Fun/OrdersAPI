from django.dispatch import Signal, receiver
from django.core.mail import EmailMultiAlternatives
from backend.models import ConfirmEmailToken, User
from django.db.models.signals import post_save
from django.conf import settings
from typing import Type
import requests

# new_user_registered = Signal()


@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User, created: bool, **kwargs):
    """
    Отправляем письмо для подтверждения регистрации через сервис smtp.bz
    """
    if created and not instance.is_active:
        print('[Signal] New user registered:', instance.pk)
        token, _ = ConfirmEmailToken.objects.get_or_create(user_id=instance.pk)
        print(
            f'Для подтверждения регистрации перейдите по ссылке: http://127.0.0.1:8000/api/user/register/confirm/?token={token.key}&email={instance.email}')
        url = 'https://api.smtp.bz/v1/smtp/send'

        headers = {
            'Authorization': '7klX2emhS70kZLdmJaFlzf0XcJGhthEpsPcj',
            'Content-Type': 'application/json'
        }

        data = {
            'from': 'no-reply@ufa-net.ru',
            'name': 'SHOP',
            'subject': 'Confirmation Email',
            'to': instance.email,
            'html': f'<html><body>Для подтверждения регистрации перейдите по ссылке: http://127.0.0.1:8000/api/user/register/confirm/?token={token.key}&email={instance.email}</body></html>'
        }

        requests.post(url, json=data, headers=headers)

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
