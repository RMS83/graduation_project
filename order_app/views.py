import requests
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator

from django.db.models import QuerySet


from rest_framework import status, generics

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
import yaml

from rest_framework.generics import GenericAPIView, ListAPIView, get_object_or_404, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from graduation_project import settings
from .utils import Util
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import jwt

from django.db import IntegrityError

from rest_framework.views import APIView

from .permissions import (IsVendorOwner, IsAdmin,
                          IsPurchaserOwner, IsVendorNoOwner, IsVendorCategoryOwner,
                          IsVendorStockOwner, IsVendorStockProductOwner, IsPurchaserNoOwner,
                          IsPurchaserRetailStoreOwner, IsVendorCartStockOwner,
                          IsPurchaserCartOwner, IsPurchaserCartPositionOwner,
                          IsVendorOrderStockOwner, IsVendorStockOrderPositionOwner, IsPurchaserOrderStatusOwner,
                          IsVendorOrderStatusOwner, IsPurchaserOrderPositionOwner)

from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (UserSerializer, UserRegisterationSerializer, UserLoginSerializer,
                          VendorSerializer, PurchaserSerializer, CategorySerializer, ProductSerializer,
                          VendorCategorySerializer, StockSerializer, CharacteristicSerializer,
                          ProductCharacteristicSerializer, RetailStoreSerializer, ShoppingCartSerializer,
                          CartPositionSerializer, OrderSerializer, OrderStatusSerializer, StatusSerializer,
                          OrderPositionSerializer)
from .models import (Vendor, Purchaser, Category, Product, VendorCategory, Stock, Characteristic,
                     ProductCharacteristic, RetailStore, ShoppingCart, CartPosition, Order,
                     OrderStatus, Status, OrderPosition)

User = get_user_model()


class UserRegisterationAPIView(GenericAPIView):
    """
    An endpoint to create a new user.
    """

    def get_permissions(self):
        return [AllowAny(), ]

    serializer_class = UserRegisterationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data
        user = User.objects.get(email=user_data["email"])
        token = RefreshToken.for_user(user)
        token_access = token.access_token
        current_site = get_current_site(request).domain
        relativeLink = reverse("email-verify")
        absurl = f"http://{current_site}{relativeLink}?token={str(token_access)}"
        email_body = f"Hi {user.email}!\nUse link below to verify your email\n\n{absurl}"
        data = {"email_body": email_body, "to_email": user.email,
                "email_subject": "Verify your email"}
        Util.send_email(data)
        user_data["tokens"] = {"refresh": str(token), "access": str(token_access)}
        return Response(user_data, status=status.HTTP_201_CREATED)


class VerifyEmail(generics.GenericAPIView):
    """
    An endpoint to verify user.
    """

    def get(self, request):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["user_id"])
            if not user.is_active:
                user.is_active = True
                user.save()
            return Response({"email": "Activated"}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            return Response({"error": "Activation Expired TimeOut"}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError:
            return Response({"error": "Invalid Token"}, status=status.HTTP_400_BAD_REQUEST)


class UserLoginAPIView(GenericAPIView):
    """
    An endpoint to authenticate users.
    """

    def get_permissions(self):
        return [AllowAny(), ]

    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        serializer = UserSerializer(user)
        token = RefreshToken.for_user(user)
        data = serializer.data
        data["tokens"] = {"refresh": str(token), "access": str(token.access_token)}
        return Response(data, status=status.HTTP_200_OK)


class UserAPIView(ListAPIView, UpdateAPIView):
    """
    An endpoint to Get, Update user information
    """
    queryset = User.objects.all()

    def get_permissions(self):
        return [IsAuthenticated()]

    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id', 'email']

    def get(self, request, *args, **kwargs):
        """
        Method Get for User
        """
        if request.user.is_staff:
            return self.list(request, *args, **kwargs)
        else:
            queryset = self.queryset.get(id=request.user.id)
            serializer = self.get_serializer(queryset)
            return Response(serializer.data)

    def get_object(self):
        """
        Returns the object the view is displaying for put/patch.
        """
        queryset = self.get_queryset().get(id=self.request.user.id)
        obj = get_object_or_404(queryset)
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    def put(self, request, *args, **kwargs):
        """
        Method PUT for User. If you aren't a superuser,
        updates available is only for yours profile.
        Only a superuser can update someone else's profile
        and assigns administrators rules.
        """
        param = self.request.query_params
        data = request.data
        if param:
            if self.request.user.is_superuser:
                if 'id' in param:
                    partial = kwargs.pop('partial', False)
                    queryset = self.get_queryset().filter(id=param['id'])
                    instance = get_object_or_404(queryset=queryset)
                    serializer = self.get_serializer(instance, data=data, partial=partial)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                    if getattr(instance, '_prefetched_objects_cache', None):
                        # If 'prefetch_related' has been applied to a queryset, we need to
                        # forcibly invalidate the prefetch cache on the instance.
                        instance._prefetched_objects_cache = {}

                    return Response(serializer.data)
                else:
                    return Response({"ERROR": ["Pass the user id in the request"]},
                                    status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"ERROR": ["Only superuser can change the parameters of another user"]},
                                status.HTTP_400_BAD_REQUEST)

        else:
            partial = kwargs.pop('partial', True)
            queryset = self.get_queryset().filter(id=self.request.user.id)
            instance = get_object_or_404(queryset=queryset)
            if 'is_staff' in data:
                return Response({"ERROR": ["Only the superuser can assign an administrator"]},
                                status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
            return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        """
        Method PATCH for User. If you aren't a superuser,
        updates available is only for yours profile.
        Only a superuser can update someone else's profile
        and assigns administrators rules.
        """
        param = self.request.query_params
        data = request.data
        if param:
            if self.request.user.is_superuser:
                if 'id' in param:
                    partial = kwargs.pop('partial', True)
                    queryset = self.get_queryset().filter(id=param['id'])
                    instance = get_object_or_404(queryset=queryset)
                    serializer = self.get_serializer(instance, data=data, partial=partial)
                    serializer.is_valid(raise_exception=True)
                    self.perform_update(serializer)
                    if getattr(instance, '_prefetched_objects_cache', None):
                        # If 'prefetch_related' has been applied to a queryset, we need to
                        # forcibly invalidate the prefetch cache on the instance.
                        instance._prefetched_objects_cache = {}
                    return Response(serializer.data)
                else:
                    return Response({"ERROR": ["Pass the user id in the request"]},
                                    status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"ERROR": ["Only superuser can change the parameters of another user"]},
                                status.HTTP_400_BAD_REQUEST)
        else:
            partial = kwargs.pop('partial', True)
            queryset = self.get_queryset().filter(id=self.request.user.id)
            instance = get_object_or_404(queryset=queryset)
            if 'is_staff' in data:
                return Response({"ERROR": ["Only the superuser can assign an administrator"]},
                                status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
            return Response(serializer.data)


class VendorViewSet(ModelViewSet):
    """
    An endpoint to vendor instance.
    """
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id', 'vendor_name']
    http_method_names = ["patch", "get", "put", "delete"]

    def get_queryset(self):
        """
        Get the list of vendor items for view.
        """
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method." % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        if self.request.user.is_staff or self.request.user.type == "purchaser":
            return queryset
        if self.request.user.type == "vendor":
            if self.action in ["retrieve", "update", "partial_update", "destroy", ]:
                return queryset
            return queryset.filter(user=self.request.user.id)

    def get_permissions(self):
        if self.action in ["list", ]:
            return [IsAuthenticated(), ]
        if self.action in ["retrieve", ]:
            GetPermission = IsAdmin | IsPurchaserNoOwner | IsVendorOwner
            return [GetPermission(), ]
        if self.action in ["update", "partial_update", ]:
            UpdatePermission = IsAdmin | IsVendorOwner
            return [UpdatePermission(), ]
        if self.action in ["destroy", ]:
            return [IsVendorOwner(), ]
        return []


class CategoryViewSet(ModelViewSet):
    """
    An endpoint to category instance.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    http_method_names = ["post", "patch", "get", "delete"]
    filterset_fields = ["id", "name", "description"]
    search_fields = ["name"]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        if self.action in ["create", ]:
            CreatePermission = IsAdmin | IsVendorNoOwner
            return [CreatePermission()]
        if self.action in ["destroy", "update", "partial_update"]:
            return [IsAdmin()]
        return []


class VendorCategoryViewSet(ModelViewSet):
    """
    An endpoint to vendor category instance.
    """
    queryset = VendorCategory.objects.all()
    serializer_class = VendorCategorySerializer
    http_method_names = ["get", "post", "delete"]
    filterset_fields = ["id", "vendor", "category", ]
    search_fields = ["vendor", "category"]

    def get_queryset(self):
        """
        Get the list of vendor_category items for view.
        """
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method." % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        if self.request.user.is_staff:
            return queryset
        if self.request.user.type == "vendor":
            if self.action in ["retrieve", "destroy", ]:
                return queryset
            return queryset.filter(vendor__user=self.request.user.id)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ["list", "retrieve", ]:
            GetPermission = IsVendorCategoryOwner | IsAdmin
            return [GetPermission(), ]
        if self.action in ["create", "destroy", ]:
            return [IsVendorCategoryOwner(), ]
        return []

    def perform_create(self, serializer):
        try:
            serializer.save(vendor=self.request.user.vendor)
        except IntegrityError:
            raise ValidationError('You already exists this category.')


class ProductViewSet(ModelViewSet):
    """
    An endpoint to product instance.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    http_method_names = ["post", "put", "patch", "get", "delete"]
    filterset_fields = ["id", "name", "category__id", "category__name"]
    search_fields = ["name"]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated(), ]
        if self.action == "create":
            CreatePermission = IsAdmin | IsVendorNoOwner
            return [CreatePermission(), ]
        if self.action in ["destroy", "update", "partial_update"]:
            return [IsAdmin(), ]
        return []

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise ValidationError('This product already exists in this category.')


class CharacteristicViewSet(ModelViewSet):
    """
    An endpoint to characteristic instance.
    """
    queryset = Characteristic.objects.all()
    serializer_class = CharacteristicSerializer
    http_method_names = ["post", "put", "get", "delete"]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated(), ]
        if self.action == "create":
            CreatePermission = IsAdmin | IsVendorNoOwner
            return [CreatePermission()]
        if self.action in ["destroy", "update", "partial_update"]:
            return [IsAdmin()]
        return []


class StockViewSet(ModelViewSet):
    """
    An endpoint to stock instance.
    """
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    http_method_names = ["post", "put", "get", "delete"]
    filterset_fields = [
        "product",
        "product__category",
        "vendor",
        "model"
    ]
    search_fields = [
        "description",
        "art",
        "product__name",
        "product__category__name",
        "vendor__name",
        "vendor__address",
        "product_characteristics__name",
    ]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ["list"]:
            return [IsAuthenticated()]
        if self.action in ["retrieve"]:
            RetrievePermission = IsAdmin | IsPurchaserNoOwner | IsVendorStockOwner
            return [RetrievePermission()]
        if self.action == "create":
            return [IsVendorNoOwner()]
        if self.action in ["update", "partial_update", "destroy"]:
            UpdateDestroyPermission = IsVendorStockOwner | IsAdmin
            return [UpdateDestroyPermission(), ]
        return []

    def get_queryset(self):
        """
        Get the list of stock items for view.
        """
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method." % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        if self.request.user.is_staff:
            return queryset.select_related("product").prefetch_related("product_characteristics")
        if self.request.user.type == "purchaser":
            return (
                queryset.filter(vendor__accepting_orders=True, quantity__gt=0).select_related(
                    "product").prefetch_related("product_characteristics")
            )
        if self.request.user.type == "vendor":
            if self.action in ["retrieve", "update", "partial_update", ]:
                return (
                    queryset.select_related("product").prefetch_related("product_characteristics")
                )
            return (
                queryset.filter(vendor__user=self.request.user).select_related("product")
                .prefetch_related("product_characteristics")
            )

    def create(self, request, *args, **kwargs):
        """
        Create a stock instance.
        """
        user = request.user
        data = request.data
        if not data.get("product"):
            return Response(
                {"ERROR": "Field Product should not be empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not Product.objects.filter(id=data.get("product")).exists():
            return Response(
                {"ERROR": "This product not exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not Category.objects.filter(vendor__user=user, products=data.get("product"), ).exists():
            return Response(
                {"ERROR": "Create category for vendor before creating or updating Stock"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        try:
            serializer.save(vendor=self.request.user.vendor)
        except IntegrityError:
            raise ValidationError('Combination of fields: model, product, vendor already exists')

class ProductCharacteristicViewSet(ModelViewSet):
    """
    An endpoint to product characteristic instance.
    """
    queryset = ProductCharacteristic.objects.all()
    serializer_class = ProductCharacteristicSerializer
    http_method_names = ["post", "patch", "get", "delete"]

    filterset_fields = [
        "stock",
        "stock__product",
        "characteristic",
    ]

    def get_queryset(self):
        """
        Get the list of stock items for view.
        """
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method." % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        if self.request.user.is_staff or self.request.user.type == "purchaser":
            return queryset
        if self.request.user.type == "vendor":
            if self.action in ["retrieve", "update", "partial_update", ]:
                return queryset
            return (
                queryset.filter(stock__vendor__user=self.request.user)
            )

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        if self.action in ["create", ]:
            return [IsVendorStockProductOwner()]
        if self.action in ["update", "partial_update", "destroy", ]:
            UpdateDestroyPermission = IsVendorStockProductOwner | IsAdmin
            return [UpdateDestroyPermission()]
        return []

    def create(self, request, *args, **kwargs):
        """
        Create a product characteristic instance.
        """
        if (
                request.data.get("stock")
                and Stock.objects.filter(id=request.data.get("stock")).exists()
        ):
            if (
                    Stock.objects.get(id=request.data.get("stock")).vendor.user
                    == request.user
            ):
                if ProductCharacteristic.objects.filter(
                        stock=request.data.get("stock"),
                        characteristic=request.data.get("characteristic"),
                ).exists():
                    return Response(
                        {"ERROR": "This stock already exists characteristic"}, )
                return super().create(request, *args, **kwargs)
            else:
                return Response(
                    {"ERROR": "You do not have permission to perform this action."},
                    status.HTTP_403_FORBIDDEN,
                )
        else:
            return Response(
                {"ERROR": '"stock" is either not indicated or such stock does not exist'},
                status.HTTP_400_BAD_REQUEST,
            )

    def update(self, request, *args, **kwargs):
        """
        Update a product characteristic instance.
        """

        if request.data.get("stock") or request.data.get("characteristic"):
            return Response(
                {"ERROR": 'Only "value" field can be amended'},
                status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)


class PurchaserViewSet(ModelViewSet):
    """
    An endpoint to purchaser instance.
    """
    queryset = Purchaser.objects.all()
    serializer_class = PurchaserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id', "purchaser_name", "user"]
    http_method_names = ["put", "put", "get", "delete", ]

    def get_queryset(self):
        """
        Get the list of vendor items for view.
        """
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method." % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        if self.request.user.is_staff or self.request.user.type == "vendor":
            return queryset
        if self.request.user.type == "purchaser":
            if self.action in ["retrieve", "update", "partial_update", "destroy", ]:
                return queryset
            return queryset.filter(user=self.request.user.id)

    def get_permissions(self):
        if self.action in ["list", ]:
            return [IsAuthenticated(), ]
        if self.action in ["retrieve", ]:
            GetPermission = IsAdmin | IsVendorNoOwner | IsPurchaserOwner
            return [GetPermission(), ]
        if self.action in ["update", "partial_update", ]:
            UpdatePermission = IsAdmin | IsPurchaserOwner
            return [UpdatePermission(), ]
        if self.action in ["destroy", ]:
            return [IsPurchaserOwner(), ]
        return []


class RetailStoreViewSet(ModelViewSet):
    """
    An endpoint to retail store instance.
    """
    queryset = RetailStore.objects.all()
    serializer_class = RetailStoreSerializer
    http_method_names = ["post", "put", "get", "delete"]

    def get_queryset(self):
        """
        Get the list of retail store items for view.
        """
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method." % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        if self.request.user.is_staff or self.request.user.type == "vendor":
            return queryset
        if self.request.user.type == "purchaser":
            if self.action in ["retrieve", "update", "partial_update", "destroy"]:
                return queryset
            return queryset.filter(purchaser__user=self.request.user)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ["list", "retrieve"]:
            ListRetrievePermission = IsAdmin | IsVendorNoOwner | IsPurchaserRetailStoreOwner
            return [ListRetrievePermission()]
        if self.action in ["update", "partial_update"]:
            return [IsPurchaserRetailStoreOwner()]
        if self.action in ["destroy"]:
            DestroyPermission = IsAdmin | IsPurchaserRetailStoreOwner
            return [DestroyPermission()]
        if self.action in ["create"]:
            return [IsPurchaserNoOwner()]
        return []

    def perform_create(self, serializer):
        try:
            serializer.save(purchaser=self.request.user.purchaser)
        except IntegrityError:
            raise ValidationError('This retail store already exists.')


class ShoppingCartViewSet(ModelViewSet):
    """
    An endpoint to shopping car instance.
    """
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    http_method_names = ["get", "delete"]

    def get_queryset(self):
        """
        Get the list of shopping cart items for view.
        """
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method." % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        if self.request.user.is_staff:
            return queryset.prefetch_related("cart_positions")
        if self.request.user.type == "purchaser":
            return queryset.filter(purchaser__user=self.request.user).prefetch_related(
                "cart_positions"
            )
        if self.request.user.type == "vendor":
            return (
                queryset.filter(cart_positions__stock__vendor__user=self.request.user)
                .distinct()
                .prefetch_related("cart_positions")
            )

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """

        if self.action in ["list", ]:
            return [IsAuthenticated()]
        if self.action in ["retrieve", ]:
            RetrievePermission = IsAdmin | IsPurchaserCartOwner | IsVendorCartStockOwner
            return [RetrievePermission()]
        if self.action in ["destroy", ]:
            return [IsPurchaserCartOwner()]
        return []

    def destroy(self, request, *args, **kwargs):
        """
        Delete all positions from shopping cart
        """

        cart_positions = CartPosition.objects.filter(shopping_cart=self.get_object())
        for position in cart_positions:
            stock = Stock.objects.get(id=position.stock.id)
            stock.quantity += position.quantity
            stock.save()
        cart_positions.delete()
        return Response({"success": f"Your shopping cart is empty"}, status.HTTP_200_OK)


class CartPositionViewSet(ModelViewSet):
    """
    An endpoint to cart position instance.
    """
    queryset = CartPosition.objects.all()
    serializer_class = CartPositionSerializer
    http_method_names = ["post", "patch", "get", "delete"]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id', "stock", "shopping_cart__purchaser", "retail_store"]

    def get_queryset(self):
        """
        Get the list of cart position items for view.
        """
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method." % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        if self.request.user.is_staff:
            return queryset.select_related("shopping_cart", "retail_store", "stock")
        if self.request.user.type == "purchaser":
            if self.action in ["retrieve", "update", "partial_update", "destroy", ]:
                return queryset.select_related("shopping_cart", "retail_store", "stock")
            return (queryset
                    .filter(shopping_cart__purchaser__user=self.request.user)
                    .select_related("shopping_cart", "retail_store", "stock")
                    )
        if self.request.user.type == "vendor":
            return (queryset
                    .filter(stock__vendor__user=self.request.user)
                    .select_related("shopping_cart", "retail_store", "stock")
                    )

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """

        if self.action in ["list", ]:
            return [IsAuthenticated()]
        if self.action in ["retrieve", ]:
            RetrievePermission = IsAdmin | IsPurchaserCartPositionOwner | IsVendorStockOrderPositionOwner
            return [RetrievePermission()]
        if self.action in ["destroy", "update", "partial_update"]:
            return [IsPurchaserCartPositionOwner()]
        if self.action in ["create", ]:
            return [IsPurchaserNoOwner()]
        return []

    def create(self, request, *args, **kwargs):
        """
        Create a cart position instance.
        """
        if not Stock.objects.filter(id=request.data["stock"]).exists():
            return Response({"ERROR": f"{request.data['stock']} stock doesn't exist"},
                            status.HTTP_400_BAD_REQUEST,
                            )
        if request.data.get("quantity"):
            if CartPosition.objects.filter(
                    stock=request.data["stock"], retail_store=request.data["retail_store"]
            ).exists():
                return Response(
                    {"ERROR": f"You already have this product in your cart "
                              f"for retail_store {request.data['retail_store']}"},
                    status.HTTP_400_BAD_REQUEST,
                )
            if not RetailStore.objects.filter(purchaser__user=request.user, id=request.data["retail_store"]).exists():
                return Response(
                    {"ERROR": "You can choose only your self retail store"},
                    status.HTTP_400_BAD_REQUEST,
                )

            stock = Stock.objects.get(id=request.data["stock"])
            if not stock.vendor.accepting_orders:
                return Response(
                    {"ERROR": "This vendor does not take new orders at the moment"},
                    status.HTTP_400_BAD_REQUEST,
                )

            quantity = int(request.data["quantity"])
            if quantity > stock.quantity:
                return Response(
                    {"ERROR": f"Not enough stock. Only {stock.quantity} is available"},
                    status.HTTP_400_BAD_REQUEST,
                )
            else:
                stock.quantity = stock.quantity - quantity
                stock.save()
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(shopping_cart=self.request.user.purchaser.shopping_cart)

    def destroy(self, request, *args, **kwargs):
        """
        Destroy a cart position instance.
        """
        cart_position = self.get_object()
        stock = Stock.objects.get(id=cart_position.stock.id)
        stock.quantity += cart_position.quantity
        stock.save()
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Update a cart position instance.
        """
        if (request.data.get("shopping_cart")
                or request.data.get("retail_store")
                or request.data.get("stock")
                or request.data.get("price")
        ):
            return Response(
                {"ERROR": f"You can change only 'quantity' field"},
                status.HTTP_400_BAD_REQUEST,
            )
        quantity = int(request.data.get("quantity"))
        cart_position = self.get_object()
        stock = Stock.objects.get(id=cart_position.stock.id)

        if quantity <= cart_position.quantity:
            stock.quantity += cart_position.quantity - quantity
            stock.save()
        else:
            if not stock.vendor.accepting_orders:
                return Response(
                    {"ERROR": f"This vendor doesn't take new orders at the moment"
                     }, status.HTTP_400_BAD_REQUEST,
                )
            if stock.quantity >= (
                    quantity - cart_position.quantity
            ):
                stock.quantity -= quantity - cart_position.quantity
                stock.save()
            else:
                return Response(
                    {"ERROR": f"Not enough stock. You can add only {stock.quantity} to your quantity"
                     }, status.HTTP_400_BAD_REQUEST,
                )
        return super().update(request, *args, **kwargs)


class OrderViewSet(ModelViewSet):
    """
    An endpoint to order instance.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ["post", "get", "delete"]

    def get_queryset(self):
        """
        Get the list of order items for view.
        """
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method." % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        if self.request.user.is_staff:
            return (queryset.prefetch_related(
                "status_order__status",
                "order_positions",
                "order_positions__stock",
                "order_positions__stock__product_characteristics",
            )
            )
        if self.request.user.type == "purchaser":
            if self.action in ["retrieve", "destroy", ]:
                return queryset.prefetch_related(
                    "status_order__status",
                    "order_positions",
                    "order_positions__stock",
                    "order_positions__stock__product_characteristics",
                )
            return (
                queryset.filter(purchaser__user=self.request.user)
                .prefetch_related(
                    "status_order__status",
                    "order_positions",
                    "order_positions__stock",
                    "order_positions__stock__product_characteristics",
                )
            )
        if self.request.user.type == "vendor":
            return (
                queryset.filter(
                    order_positions__stock__vendor__user=self.request.user)
                .distinct()
                .prefetch_related(
                    "status__orders__status",
                    "order_positions",
                    "order_positions__stock",
                    "order_positions__stock__product_characteristics",
                )
            )

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ["list", ]:
            return [IsAuthenticated()]
        if self.action in ["retrieve"]:
            RetrievePermission = IsAdmin | IsPurchaserCartOwner | IsVendorOrderStockOwner
            return [RetrievePermission()]
        if self.action in ["destroy"]:
            return [IsPurchaserCartOwner()]
        if self.action in ["create"]:
            return [IsPurchaserNoOwner()]
        return []

    def create(self, request, *args, **kwargs):
        """
        Create an order instance and order position instances based on shopping cart instance and cart position
        instances
        """

        user = request.user
        purchaser = user.purchaser
        cart_positions = purchaser.shopping_cart.cart_positions.all()
        if not cart_positions.count():
            return Response(
                {"error": "Your shopping cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        order = purchaser.orders.get(id=serializer.data["id"])
        vendors = {}
        for position in cart_positions:
            new_position = OrderPosition.objects.create(
                order=order,
                retail_store=position.retail_store,
                stock=position.stock,
                quantity=position.quantity,
                price=position.price,
            )
            if new_position.stock.vendor.user not in vendors:
                vendors[new_position.stock.vendor.user] = [
                    {
                        "id": new_position.id,
                        "order": order.id,
                        "stock": new_position.stock,
                        "quantity": new_position.quantity,
                        "price": new_position.price,
                    }
                ]
            else:
                vendors[new_position.stock.vendor.user].append(
                    {
                        "id": new_position.id,
                        "order": order.id,
                        "stock": new_position.stock,
                        "quantity": new_position.quantity,
                        "price": new_position.price,
                    }
                )

        cart_positions.delete()
        for vendor, positions in vendors.items():
            text = "New orders\n"
            for position in positions:
                text += f'''Order #{position["order"]}, stock {position["stock"].product.name},
                       quantity {position["quantity"]}, price {position["price"]}\n'''
            text += "Go to the app and confirm the order"

            data = {"email_body": text, "to_email": vendor.email,
                    "email_subject": "New order"}
            Util.send_email(data)

        response = serializer.data.copy()

        text_for_purchaser = f"""Thank you for order.\n
                   Your order #{response["id"]}.\n
                   Total amount of {order.amount}.\n
                   Status of your order will automatically update after vendors confirmation"""
        data = {"email_body": text_for_purchaser, "to_email": user.email,
                "email_subject": "Thank you for your order"}
        Util.send_email(data)

        return Response(response, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(purchaser=self.request.user.purchaser)

    def destroy(self, request, *args, **kwargs):
        """
        Set to cancelled an order instance.
        """
        instance = self.get_object()
        order_status = OrderStatus.objects.filter(order=instance)
        if order_status.exists():
            if order_status.filter(status__name="Отменен").exists():
                return Response(
                    {"ERROR": "Order is already cancelled"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"ERROR": "Your can cancel only full unconfirmed and undelivered orders"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            OrderStatus.objects.create(order=instance, status_id=Status.objects.get(name="Отменен").id)
        except:
            return Response(
                {"ERROR": "NOT DELETE! The status table must have a field: 'Отменен'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for position in instance.order_positions.all():
            stock = Stock.objects.get(id=position.stock.id)
            stock.quantity += position.quantity
            stock.save()
        return Response({"SUCCESS": "Order cancelled"}, status.HTTP_200_OK)


class StatusViewSet(ModelViewSet):
    """
    An endpoint to status instance.
    """
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', "orders"]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return []


class OrderStatusViewSet(ModelViewSet):
    """
    An endpoint to order status instance.
    """
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer
    http_method_names = ["get", "patch", "delete"]
    filterset_fields = ['order', "status"]

    def get_queryset(self):
        """
        Get the list of order status items for view.
        """
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method." % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        if self.request.user.is_staff:
            return queryset.prefetch_related("order__order_positions__retail_store")
        if self.request.user.type == "purchaser":
            if self.action in ["retrieve"]:
                return queryset.prefetch_related("order__order_positions__retail_store")
            return (
                queryset.filter(order__purchaser__user=self.request.user)
                .prefetch_related("order__order_positions__retail_store")
            )
        if self.request.user.type == "vendor":
            if self.action in ["retrieve"]:
                return queryset.prefetch_related("order__order_positions__retail_store")
            return (
                queryset.filter(order__order_positions__stock__vendor__user=self.request.user)
                .prefetch_related("order__order_positions__retail_store")
            )

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ["retrieve", "list", ]:
            RetrievePermission = IsPurchaserOrderStatusOwner | IsAdmin | IsVendorOrderStatusOwner
            return [RetrievePermission()]
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return []


class OrderPositionViewSet(ModelViewSet):
    """
    An endpoint to order position instance.
    """
    queryset = OrderPosition.objects.all()
    serializer_class = OrderPositionSerializer
    http_method_names = ["patch", "get"]
    filterset_fields = ["confirmed", "delivered", "order"]

    def get_queryset(self):
        """
        Get the list of order position items for view.
        """
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method." % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        if self.request.user.is_staff:
            return (queryset
                    .prefetch_related("stock",
                                      "stock__characteristics__product_characteristics",
                                      "order__status_order")
                    )
        if self.request.user.type == "purchaser":
            if self.action in ["list", ]:
                return (queryset
                        .filter(order__purchaser__user=self.request.user)
                        .prefetch_related("stock",
                                          "stock__characteristics__product_characteristics",
                                          "order__status_order")
                        )
            else:
                return (queryset
                        .prefetch_related("stock",
                                          "stock__characteristics__product_characteristics",
                                          "order__status_order")
                        )

        if self.request.user.type == "vendor":
            if self.action in ["list", ]:
                return (queryset
                        .filter(stock__vendor__user=self.request.user)
                        .prefetch_related("stock",
                                          "stock__characteristics__product_characteristics",
                                          "order__status_order")
                        )
            else:
                return (queryset
                        .prefetch_related("stock",
                                          "stock__characteristics__product_characteristics",
                                          "order__status_order")
                        )

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """

        if self.action in ["list", ]:
            return [IsAuthenticated()]
        if self.action in ["retrieve", ]:
            RetrievePermission = IsAdmin | IsPurchaserOrderPositionOwner | IsVendorStockOrderPositionOwner
            return [RetrievePermission()]
        if self.action in ["destroy", "update", "partial_update"]:
            return [IsVendorStockOrderPositionOwner()]
        return []

    def update(self, request, *args, **kwargs):
        """
        Update an order position instance (confirm or/and deliver).
        """
        data = request.data
        if "confirmed" not in data and "delivered" not in data:
            return Response(
                {"ERROR": "You can change only confirmed or/and delivered status"},
                status.HTTP_400_BAD_REQUEST)
        instance = self.get_object()
        if OrderStatus.objects.filter(order_id=instance.order.id, status__name="Отменен").exists():
            return Response(
                {"ERROR": "This order already cancelled"},
                status.HTTP_400_BAD_REQUEST,
            )

        if "confirmed" in data:
            if data["confirmed"]:
                if not instance.confirmed:
                    instance.confirmed = True
                    if not OrderStatus.objects.filter(
                            order=instance.order,
                            status=Status.objects.get(name="Частично подтвержден")).exists():
                        OrderStatus.objects.create(order=instance.order,
                                                   status=Status.objects.get(name="Частично подтвержден"))

                    instance.save()
                    if (OrderPosition.objects.filter(order=instance.order.id, confirmed=True).count() ==
                            OrderPosition.objects.filter(order=instance.order.id, ).count()):
                        order_status = OrderStatus.objects.get(order=instance.order,
                                                               status=Status.objects.get(name="Частично подтвержден"))
                        OrderStatus.__setattr__(order_status, "status", Status.objects.get(name="Подтвержден"))
                        order_status.save()

            elif not data["confirmed"]:
                if instance.confirmed:
                    return Response(
                        {"ERROR": "You can't fulfill this request, the position already confirmed"},
                        status.HTTP_400_BAD_REQUEST,
                    )

        if "delivered" in data:
            if data["delivered"]:
                if not instance.confirmed:
                    return Response(
                        {"ERROR": "You can't set status 'delivered' before confirmation"},
                        status.HTTP_400_BAD_REQUEST,
                    )
                if not instance.delivered:
                    instance.delivered = True
                    if not OrderStatus.objects.filter(
                            order_id=instance.order.id,
                            status=Status.objects.get(name="Частично доставлен")).exists():
                        OrderStatus.objects.create(order=instance.order,
                                                   status=Status.objects.get(name="Частично доставлен"))
                    instance.save()
                    if (OrderPosition.objects.filter(order=instance.order.id,
                                                     delivered=True).count() ==
                            OrderPosition.objects.filter(order=instance.order.id, ).count()):
                        order_status = OrderStatus.objects.get(order=instance.order,
                                                               status=Status.objects.get(name="Частично доставлен"))
                        OrderStatus.__setattr__(order_status, "status", Status.objects.get(name="Доставлен"))
                        order_status.save()

            elif not data["delivered"]:
                if instance.delivered:
                    return Response(
                        {"ERROR": "You can't cancel the delivered"},
                        status.HTTP_400_BAD_REQUEST,
                    )

        if "delivered" in data and not data["delivered"] and "confirmed" in data and not data["confirmed"]:
            return Response(
                {"SUCCESS": "Pass the correct parameters"}, status.HTTP_200_OK
            )
        return Response(
            {"SUCCESS": "Оrder position successfully amended"}, status.HTTP_200_OK
        )


class ImportView(APIView):
    """
    An endpoint to update price instance.
    """

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"STATUS": "User not authenticated"}, status.HTTP_403_FORBIDDEN
            )

        if request.user.type != 'vendor':
            return Response(
                {"STATUS": "Only for Vendor"}, status.HTTP_403_FORBIDDEN)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except:
                return Response({"STATUS": "Not valid URL"}, status.HTTP_403_FORBIDDEN)

            import_file = requests.get(url).content
            data = yaml.safe_load(import_file)

            try:
                user = data["user"][0]["id"]
                vendor = data["vendor"][0]["id"]
                if user != request.user.id:
                    return Response({"STATUS": "Not valid USER"}, status.HTTP_403_FORBIDDEN)
            except:
                return Response({"STATUS": "Specify self user id and vendor id in yaml"}, status.HTTP_403_FORBIDDEN)

            for category in data["categories"]:
                category, _ = Category.objects.get_or_create(name=category["name"],
                                                             description=category["description"])
                vendor_category, _ = VendorCategory.objects.get_or_create(
                    category_id=category.id, vendor_id=vendor)

            for stock in data["stock"]:
                try:
                    category = Category.objects.get(name=stock["category"])
                except:
                    return Response(
                        {"ERROR": f"Non-existent category in the stock with product art {stock['art']}"}
                    )

                product, _ = Product.objects.get_or_create(name=stock["product"], category=category)

                try:
                    stock_prod = Stock.objects.get(art=stock["art"],
                                                   model=stock["model"],
                                                   product=product,
                                                   vendor=Vendor.objects.get(id=vendor)
                                                   )
                    stock_prod.description = stock["description"]
                    stock_prod.price = stock["price"]
                    stock_prod.price_rrc = stock["price_rrc"]
                    stock_prod.quantity = stock["quantity"]
                    stock_prod.save()
                except:
                    stock_prod = Stock.objects.create(art=stock["art"],
                                                      model=stock["model"],
                                                      product=product,
                                                      vendor=Vendor.objects.get(id=vendor),
                                                      description=stock["description"],
                                                      price=stock["price"],
                                                      price_rrc=stock["price_rrc"],
                                                      quantity=stock["quantity"]
                                                      )

                for name, value in stock['product_characteristics'].items():
                    characteristic, _ = Characteristic.objects.get_or_create(name=name)
                    product_characteristic, _ = (
                        ProductCharacteristic.objects.get_or_create(stock=stock_prod,
                                                                    characteristic=characteristic,
                                                                    value=value))

            return Response(
                {"STATUS": "Ok"}, status.HTTP_200_OK
            )
        return Response({"ERROR": "All necessary arguments are not specified"})
