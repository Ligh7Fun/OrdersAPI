from django.contrib.auth import authenticate
from django.core.validators import URLValidator
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle
from django.urls import reverse
from backend.models import ConfirmEmailToken
from rest_framework.authtoken.models import Token

from .models import Shop, Category, ProductInfo, Product, Parameter, ProductParameter
from .permissions import IsShopOwner
from requests import get
from yaml import load as load_yaml, Loader

from .serializers import UserSerializer


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от партнера
    """

    permission_classes = [IsShopOwner, IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request, *args, **kwargs):
        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValueError as e:
                return Response({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content
                data = load_yaml(stream, Loader=Loader)
                shop, _ = Shop.objects.get_or_create(
                    name=data['shop'],
                    user_id=request.user.pk
                )

                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(
                        id=category['id'],
                        name=category['name'],
                    )
                    category_object.shops.add(shop.pk)
                    category_object.save()

                ProductInfo.objects.filter(shop_id=shop.pk).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(
                        name=item['name'],
                        category_id=item['category'],
                    )

                    product_info = ProductInfo.objects.create(
                        product_id=product.pk,
                        external_id=item['id'],
                        model=item['model'],
                        price=item['price'],
                        price_rrc=item['price_rrc'],
                        quantity=item['quantity'],
                        shop_id=shop.pk,
                    )
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(
                            name=name,

                        )
                        ProductParameter.objects.create(
                            product_info_id=product_info.pk,
                            parameter_id=parameter_object.pk,
                            value=value,
                        )

                return Response({'Status': True})

        return Response({'Status': False, 'Error': 'Неверная ссылка или данные отсутствуют'})


class RegisterAccount(APIView):
    """
    Класс для регистрации аккаунта
    """

    authentication_classes = []
    permission_classes = []
    throttle_classes = [UserRateThrottle]
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            user.set_password(request.data.get('password'))
            user.save()

            # TEST
            # Создание токена подтверждения
            token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.pk)
            # Формирование ссылки для подтверждения
            confirmation_link = f'http://127.0.0.1:8000/api/user/register/confirm/?token={token.key}&email={user.email}'
            # TEST

            return Response({'Status': True, 'Link': confirmation_link})
        else:
            return Response({'Status': False, 'Errors': user_serializer.errors})


"""
{
    "Status": true,
    "Link": "http://127.0.0.1:8000/api/user/register/confirm/?token=3df332ed96d459a526920777801291528fce&email=m5221710@gmail.com"
}"""


class ConfirmAccount(APIView):
    """
    Класс для подтверждения почты
    """

    authentication_classes = []
    permission_classes = []
    throttle_classes = [UserRateThrottle]

    def post(self, request, *args, **kwargs):
        confirmation_token = request.data.get('token')
        email = request.data.get('email')
        if not confirmation_token or not email:
            return Response({'Status': False, 'Error': 'Не указаны необходимые данные!'})
        token = ConfirmEmailToken.objects.filter(user__email=email, key=confirmation_token).first()
        if token:
            token.user.is_active = True
            token.user.save()
            token.delete()
            return Response({'Status': True})
        else:
            return Response({'Status': False, 'Error': 'Пользователь уже активирован или ссылка некорректна'})


class LoginAccount(APIView):
    """
    Класс для авторизации пользователя
    """

    authentication_classes = []
    permission_classes = []
    throttle_classes = [UserRateThrottle]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if email and password:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return Response({'Status': True, 'Token': token.key})
        else:
            return Response({'Status': False, 'Error': 'Не указан email или пароль'})

        return Response({'Status': False, 'Error': 'Не удалось авторизоваться'})
