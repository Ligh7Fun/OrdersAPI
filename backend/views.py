from django.core.validators import URLValidator
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle

from .models import Shop, Category, ProductInfo, Product, Parameter, ProductParameter
from .permissions import IsShopOwner
from requests import get
from yaml import load as load_yaml, Loader


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
