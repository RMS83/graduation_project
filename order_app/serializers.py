from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.validators import MinValueValidator
from rest_framework import serializers

from order_app.models import (User, Vendor, Purchaser, Category, VendorCategory,
                              Product, Stock, Characteristic,
                              ProductCharacteristic, RetailStore,
                              CartPosition, ShoppingCart, Order,
                              Status, OrderStatus, OrderPosition)


class UserRegisterationSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize registration requests and create a new user.
    """

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "password", "type"]

        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer class to authenticate users with email and password.
    """
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize CustomUser model.
    """
    type_id = serializers.SerializerMethodField(read_only=True)

    def get_type_id(self, obj):
        if obj.type == "vendor":
            return obj.vendor.id
        if obj.type == "purchaser":
            return obj.purchaser.id
        if obj.type == "owner":
            return "Owner"

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "password", "type", "type_id",
                  "is_active", "is_staff", "is_superuser", "date_joined"
                  ]
        extra_kwargs = {"password": {"write_only": True},
                        "is_superuser": {"read_only": True},
                        "type": {"read_only": True},
                        "type_id": {"read_only": True},
                        }

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(**validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("password"):
            validated_data["password"] = make_password(validated_data["password"])
        return super().update(instance, validated_data)


class VendorSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize vendor instances
    """

    class Meta:
        model = Vendor
        fields = ["id", "vendor_name", "vendor_phone", "accepting_orders", "vendor_address", "user"]
        read_only_fields = ["user", ]


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize category instances
    """

    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class VendorCategorySerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize vendor category instances
    """
    quantity_products = serializers.IntegerField(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    vendor_name = serializers.CharField(source="vendor.vendor_name", read_only=True)

    class Meta:
        model = VendorCategory
        fields = ["id", "vendor", "vendor_name", "category", "category_name", "quantity_products", ]
        read_only_fields = ["vendor", ]


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize product instances
    """

    class Meta:
        model = Product
        fields = ["id", "name", "category"]


class CharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize characteristic instances
    """

    class Meta:
        model = Characteristic
        fields = ["id", "name", ]


class ProductCharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize product characteristic instances
    """
    product_name = serializers.CharField(source="stock.product.name", read_only=True)
    characteristic_name = serializers.CharField(source="characteristic.name", read_only=True)
    product_model = serializers.CharField(source="stock.model", read_only=True)

    class Meta:
        model = ProductCharacteristic
        fields = ["id", "stock", "product_name", "product_model", "characteristic", "characteristic_name", "value"]


class StockSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize stock instances
    """
    description = serializers.CharField(required=False)
    product_characteristics = serializers.StringRelatedField(read_only=True, many=True)

    class Meta:
        model = Stock
        fields = [
            "id",
            "art",
            "model",
            "description",
            "price",
            "price_rrc",
            "quantity",
            "vendor",
            "product",
            "product_characteristics"

        ]
        read_only_fields = ["vendor", ]


class RetailStoreSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize retail store instances
    """

    class Meta:
        model = RetailStore
        fields = ["id", "purchaser", "store_name", "store_address", "store_phone"]
        read_only_fields = ["purchaser", ]


class RetailStoreForPurchaserSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize purchasers retail store instances
    """

    class Meta:
        model = RetailStore
        fields = ["id", "store_name", "store_address", "store_phone"]


class PurchaserSerializer(serializers.ModelSerializer):
    retail_stores = RetailStoreForPurchaserSerializer(read_only=True, many=True)

    class Meta:
        model = Purchaser
        fields = ['id', 'user', 'purchaser_name', 'purchaser_phone', 'purchaser_address', "retail_stores"]
        read_only_fields = ['user', "retail_stores"]


class CartPositionSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize cart position instances
    """
    quantity = serializers.IntegerField(min_value=1, help_text="Обязательное поле, количество должно быть больше 0")

    price = serializers.DecimalField(
        decimal_places=2,
        max_digits=10,
        validators=[MinValueValidator(0.01)],
        default=0, read_only=True)

    class Meta:
        model = CartPosition
        fields = ["id", "shopping_cart", "retail_store", "stock", "quantity", "price", "amount"]
        read_only_fields = ["amount",
                            "shopping_cart",
                            ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize shopping cart instances
    """

    # cart_positions = CartPositionSerializer(many=True)

    class Meta:
        model = ShoppingCart
        fields = ["id", "purchaser", "total_quantity", "total_amount", "cart_positions", ]


class StatusSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize status instances
    """

    class Meta:
        model = Status
        fields = ["id", "name", ]


class OrderStatusSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize status for order instances
    """
    status = StatusSerializer()

    class Meta:
        model = OrderStatus
        fields = ["id", "order", "status", "created_at", ]


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize order instances
    """
    status = StatusSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "purchaser",
            "created_at",
            "amount",
            "status",
        ]
        read_only_fields = [
            "created_at",
            "purchaser",
            "amount",
            "status",
        ]


class OrderPositionSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize order position instances
    """

    stock = StockSerializer(read_only=True)
    confirmed = serializers.BooleanField(default=False)
    delivered = serializers.BooleanField(default=False)

    class Meta:
        model = OrderPosition
        fields = [
            "id",
            "order",
            "stock",
            "quantity",
            "price",
            "confirmed",
            "delivered",
            "amount",
        ]
        read_only_fields = ["order", "stock", "quantity", "price", "amount"]
