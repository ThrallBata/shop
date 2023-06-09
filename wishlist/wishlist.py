from decimal import Decimal
import copy

from django.conf import settings
from shop.models import Product


class Wishlist(object):

    def __init__(self, request):
        """
        Инициализируем корзину
        """
        self.session = request.session
        wishlist = self.session.get(settings.WISHLIST_SESSION_ID)
        if not wishlist:
            # save an empty wishlist in the session
            wishlist = self.session[settings.WISHLIST_SESSION_ID] = {}
        self.wishlist = wishlist

    def __iter__(self):
        """
        Перебор элементов в корзине и получение продуктов из базы данных.
        """
        product_slug = self.wishlist.keys()
        # получение объектов product и добавление их в корзину
        products = Product.objects.filter(id__in=product_slug)
        wishlist = copy.deepcopy(self.wishlist)
        for product in products:
            wishlist[str(product.id)]['product'] = product

        for item in wishlist.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Подсчет всех товаров в корзине.
        """
        return sum(item['quantity'] for item in self.wishlist.values())

    def add(self, product, quantity=1, update_quantity=False):
        """
        Добавить продукт в корзину или обновить его количество.
        """
        product_id = str(product.id)
        if product_id not in self.wishlist:
            self.wishlist[product_id] = {'quantity': 0,
                                         'price': str(product.price)}
        self.wishlist[product_id]['quantity'] = quantity
        self.save()

    def save(self):
        # Обновление сессии cart
        self.session[settings.WISHLIST_SESSION_ID] = self.wishlist
        # Отметить сеанс как "измененный", чтобы убедиться, что он сохранен
        self.session.modified = True

    def remove(self, product):
        """
        Удаление товара из корзины.
        """
        product_id = str(product.id)
        if product_id in self.wishlist:
            del self.wishlist[product_id]
            self.save()

    def get_total_price(self):
        """
        Подсчет стоимости товаров в корзине.
        """
        return sum(Decimal(item['price']) * item['quantity'] for item in
                   self.wishlist.values())

    def clear(self):
        # удаление корзины из сессии
        del self.session[settings.WISHLIST_SESSION_ID]
        self.session.modified = True
