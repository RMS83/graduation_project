from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, MinValueValidator



# _____________________________Область пользователя__________________________

REGEXPhone = RegexValidator(regex=r"(?<!\S)(?:[+][7])[(]\d{3}[)]\d{3}[-]\d{2}[-]\d{2}(?!\S)")

USER_TYPE_CHOICES = (
    ("purchaser", "Покупатель"),
    ("vendor", "Поставщик"),
)

class UserManager(BaseUserManager):

    def create_user(
            self, email, first_name, last_name,
            password=None,
            type=USER_TYPE_CHOICES[0][0],
            commit=True
    ):
        """
        Creates and saves a User with the given email, first name, last name, choices type
        and password.
        """
        if not email:
            raise ValueError(_("Users must have an email address"))
        if not first_name:
            raise ValueError(_("Users must have a first name"))
        if not last_name:
            raise ValueError(_("Users must have a last name"))
        if type not in (i[0] for i in USER_TYPE_CHOICES):
            raise ValueError(_("Users must have a type. Type can be a purchaser or a vendor"))

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            type=type
        )

        user.set_password(password)

        if commit:
            user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password):
        """
        Creates and saves a superuser with the given email, first name,
        last name and password.
        """
        user = self.create_user(
            email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            commit=False,
        )
        user.is_staff = True
        user.is_superuser = True
        user.type = "owner"
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Class for describing users. Using an email address as a token identification instead of a username.
    """
    objects = UserManager()

    # The field of the model that is used as a unique identifier
    USERNAME_FIELD = "email"

    # List of field names that will be requested when creating a superuser
    REQUIRED_FIELDS = ["first_name", "last_name"]

    email = models.EmailField(
        verbose_name=_("email address"), max_length=255, unique=True
    )

    # last_login field supplied by AbstractBaseUser
    first_name = models.CharField(_("first name"), max_length=30, blank=True)
    last_name = models.CharField(_("last name"), max_length=100, blank=True)

    type = models.CharField(verbose_name="User type",
                            choices=USER_TYPE_CHOICES,
                            max_length=9
                            )

    is_active = models.BooleanField(
        _("active"),
        default=False,
        help_text=_(
            "Indicates whether this user should be considered active."
            "Uncheck this box instead of deleting accounts."
        ),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_(
            "Specifies whether the user can log in to the API as an administrator."
        ),
    )

    date_joined = models.DateTimeField(
        _("date joined"), default=timezone.now
    )

    def full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def __str__(self):
        return "%s <%s>" % (self.full_name(), self.email)

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("id",)


# _____________________________Область продавца__________________________

class Vendor(models.Model):
    """
    Class for describing vendors
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vendor_name = models.CharField(max_length=50)
    vendor_phone = models.CharField(validators=[REGEXPhone], max_length=16,
                                    help_text=_(
                                        "Format phone: +7(999)999-99-99"))
    accepting_orders = models.BooleanField(default=True)
    vendor_address = models.CharField(max_length=200, null=True, blank=True,
                                      help_text=_(
                                          "Exemple: 127549, Москва, Алтуфьевское шоссе, 64В, пом.5")
                                      )

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"

    @property
    def representations(self):
        """
        Return the .__class__ plus the user.full_name plus the vendor_name.
        """
        representation = "id: %s, %s" % (self.id, self.vendor_name)
        return representation.strip()

    def __str__(self):
        return self.representations


class Category(models.Model):
    """
    Class for describing the product categories
    """
    name = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    vendor = models.ManyToManyField(Vendor, blank=True, through="VendorCategory")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Список категорий"
        ordering = ("name",)

    def __str__(self):
        return self.name


class VendorCategory(models.Model):
    """
    Class for describing the vendor's product categories
    """
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="categories")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="categories")

    @property
    def quantity_products(self):
        return self.vendor.stocks.filter(product__category=self.category).count()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "category", ], name="unique_category_vendor"
            ),
        ]
        ordering = ("category",)

    def __str__(self):
        return f"{self.quantity_products} товаров в категории {self.category.name} у {self.vendor.vendor_name}"


class Product(models.Model):
    """
    Class for describing products
    """

    name = models.CharField(max_length=50)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Список продуктов"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "category", ], name="unique_category_product"
            ),
        ]
        ordering = ("name", )

    def __str__(self):
        return self.name


class Stock(models.Model):
    """
    Class for describing stock of certain product on warehouse of certain supplier
    """
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="stocks"
    )
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="stocks"
    )

    art = models.CharField(max_length=30)
    model = models.CharField(max_length=80)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(
        decimal_places=2, max_digits=10, validators=[MinValueValidator(0.01)]
    )
    price_rrc = models.DecimalField(
        decimal_places=2, max_digits=10, validators=[MinValueValidator(0.01)]
    )
    quantity = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Продукт на складе"
        verbose_name_plural = "Список продуктов на складе"
        constraints = [
            models.UniqueConstraint(
                fields=["model", "product", "vendor"], name="unique_stock"
            ),
        ]
        ordering = ("product", "price")

    def __str__(self):
        return f"Запас {self.product.name} {self.model} у {self.vendor}"


class Characteristic(models.Model):
    """
    Class for describing products characteristics
    """

    name = models.CharField(max_length=50, unique=True)
    stock = models.ManyToManyField(Stock, related_name="characteristics", through="ProductCharacteristic")

    class Meta:
        verbose_name = "Характеристика"
        verbose_name_plural = "Список характеристик"
        ordering = ("-name",)

    def __str__(self):
        return self.name


class ProductCharacteristic(models.Model):
    """
    Class for describing certain characteristic of certain stock of products
    """
    characteristic = models.ForeignKey(
        Characteristic, on_delete=models.CASCADE, related_name="product_characteristics"
    )

    stock = models.ForeignKey(
        Stock, on_delete=models.CASCADE, related_name="product_characteristics"
    )

    value = models.CharField(max_length=30)

    class Meta:
        verbose_name = "Характеристика продукта на складе"
        verbose_name_plural = "Список характеристик на складе"
        constraints = [
            models.UniqueConstraint(
                fields=["stock", "characteristic", "value"], name="unique_product_characteristic"
            ),
        ]
        ordering = ("stock", "value")

    def __str__(self):
        return f"{self.characteristic}: {self.value}"


# _____________________________Область покупателя__________________________

class Purchaser(models.Model):
    """
    Class for describing purchasers
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    purchaser_name = models.CharField(max_length=50)
    purchaser_phone = models.CharField(validators=[REGEXPhone], max_length=16,
                                       help_text=_(
                                           "Format phone: +7(999)999-99-99"))
    purchaser_address = models.CharField(max_length=200, null=True, blank=True,
                                         help_text=_(
                                             "Main offices address. "
                                             "Exemple: 127549, Москва, Алтуфьевское шоссе, 64В, пом.5"
                                         ))

    class Meta:
        verbose_name = "Покупатель"
        verbose_name_plural = "Покупатели"

    @property
    def representations(self):
        """
        Return the .__class__ plus the user.full_name plus the purchaser_name.
        """
        representation = "id: %s, %s" % (self.id, self.purchaser_name, )
        return representation.strip()

    def __str__(self):
        return self.representations


class RetailStore(models.Model):
    purchaser = models.ForeignKey(Purchaser, on_delete=models.CASCADE, related_name="retail_stores")
    store_name = models.CharField(max_length=60, )
    store_address = models.CharField(max_length=200, blank=True,
                                     help_text=_(
                                         "Exemple: 127549, Москва, Алтуфьевское шоссе, 64В, пом.5"
                                     )
                                     )
    store_phone = models.CharField(validators=[REGEXPhone], max_length=16,
                                   help_text=_(
                                       "Format phone: +7(999)999-99-99"), unique=True)

    class Meta:
        verbose_name = "Розничный магазин"
        verbose_name_plural = "Список розничных магазинов"
        constraints = [
            models.UniqueConstraint(
                fields=["store_name", "store_address"], name="unique_store"
            ),
        ]
        ordering = ("store_name",)

    def __str__(self):
        return f"Магазин {self.store_name}, {self.store_address}"


class ShoppingCart(models.Model):
    """
    Class for describing purchasers shopping cart
    """

    purchaser = models.OneToOneField(
        Purchaser, on_delete=models.CASCADE, related_name="shopping_cart")

    stock = models.ManyToManyField(
        Stock, through="CartPosition", related_name="shopping_cart")

    def _calculate_quantity(self) -> int:
        """
        Calculates quantity of items in shopping cart
        :return: total quantity of items
        """
        return sum([position.quantity for position in self.cart_positions.all()])

    @property
    def total_quantity(self) -> int:
        """
        Sets total_quantity field of shopping cart instance
        :return: total quantity of items
        """
        return self._calculate_quantity()

    def _calculate_amount(self):
        """
        Calculates total amount of shopping cart
        :return: total amount for items
        """
        return sum([position.amount for position in self.cart_positions.all()])

    @property
    def total_amount(self) -> Decimal:
        """
        Sets total_amount field of shopping cart instance
        :return: total amount
        """
        return self._calculate_amount()

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Список корзин"
        ordering = ("id",)

    def __str__(self):
        return f"Корзина покупателя {self.purchaser.purchaser_name}"


class CartPosition(models.Model):
    """
    Class for describing products positions in purchasers cart
    """

    shopping_cart = models.ForeignKey(
        ShoppingCart, on_delete=models.CASCADE, related_name="cart_positions"
    )
    stock = models.ForeignKey(
        Stock, on_delete=models.CASCADE, related_name="cart_positions"
    )

    retail_store = models.ForeignKey(
        RetailStore, on_delete=models.CASCADE, related_name="cart_positions"
    )

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])

    @property
    def price(self):
        return self.stock.price

    @property
    def amount(self) -> Decimal:
        """
        Calculates and setts amount field of cart position instance
        :return: total amount (quantity * price)
        """
        return self.quantity * self.price

    class Meta:
        verbose_name = "Позиция в корзине"
        verbose_name_plural = "Список позиций в корзине"
        constraints = [
            models.UniqueConstraint(
                fields=["shopping_cart", "stock", "retail_store"], name="unique_shopping_cart_stock"
            ),
        ]
        ordering = ("shopping_cart",)


class Order(models.Model):
    """
    Class for describing order
    """

    purchaser = models.ForeignKey(
        Purchaser, on_delete=models.CASCADE, related_name="orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    stock = models.ManyToManyField(
        Stock, through="OrderPosition", related_name="orders")

    @property
    def amount(self) -> Decimal:
        """
        Sets total_amount field of order instance
        :return: total amount of order
        """
        return sum([position.amount for position in self.order_positions.all()])

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Список заказов"
        ordering = ("-created_at", "purchaser")

    def __str__(self):
        return f"Заказ {self.id} создан: {self.created_at}. Статус: {self.status.name}"


class Status(models.Model):
    """
    Class for describing Status
    """
    name = models.CharField(max_length=20, null=False, unique=True)
    orders = models.ManyToManyField(Order, related_name="status", through="OrderStatus")

    class Meta:
        verbose_name = "Статус"
        verbose_name_plural = "Список статусов"
        ordering = ("name",)

    def __str__(self):
        return self.name


class OrderStatus(models.Model):
    """
    Class for describing the relationship of orders and their statuses
    """
    order = models.ForeignKey(Order, on_delete=models.RESTRICT, related_name="status_order")
    status = models.ForeignKey(Status, on_delete=models.RESTRICT, related_name="status_order")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Статус заказа"
        verbose_name_plural = "Список статусов заказа"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.order.id} {self.status.name}"


class OrderPosition(models.Model):
    """
    Class for describing products positions in purchasers cart
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_positions"
    )
    stock = models.ForeignKey(
        Stock, on_delete=models.CASCADE, related_name="order_positions"
    )

    retail_store = models.ForeignKey(
        RetailStore, on_delete=models.CASCADE, related_name="order_positions"
    )

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])

    price = models.DecimalField(
        decimal_places=2, max_digits=10, validators=[MinValueValidator(0.01)], default=0
    )

    confirmed = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)

    @property
    def amount(self) -> Decimal:
        """
        Calculates and setts amount field of cart position instance
        :return: total amount (quantity * price)
        """
        return self.quantity * self.price

    class Meta:
        verbose_name = "Позиция в заказе"
        verbose_name_plural = "Список позиций в заказе"
        constraints = [
            models.UniqueConstraint(
                fields=["order", "stock", "retail_store"], name="unique_order_stock_retail_store"
            ),
        ]
        ordering = ("order",)
