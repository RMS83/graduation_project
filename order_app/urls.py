from rest_framework.routers import DefaultRouter

from order_app.views import (PurchaserViewSet, VendorViewSet, CategoryViewSet, VendorCategoryViewSet, ProductViewSet,
                             CharacteristicViewSet, ProductCharacteristicViewSet, RetailStoreViewSet,
                             ShoppingCartViewSet, CartPositionViewSet, OrderViewSet, StatusViewSet, OrderStatusViewSet,
                             OrderPositionViewSet, StockViewSet)

app_name = "oder_app"

router = DefaultRouter()
router.register("vendors", VendorViewSet)
router.register("categories", CategoryViewSet)
router.register("vendor_categories", VendorCategoryViewSet)
router.register("products", ProductViewSet)
router.register("characteristics", CharacteristicViewSet)
router.register("product_characteristics", ProductCharacteristicViewSet)
router.register("purchasers", PurchaserViewSet)
router.register("retail_stores", RetailStoreViewSet)
router.register("shopping_carts", ShoppingCartViewSet)
router.register("cart_positions", CartPositionViewSet)
router.register("orders", OrderViewSet)
router.register("status", StatusViewSet)
router.register("order_status", OrderStatusViewSet)
router.register("order_position", OrderPositionViewSet)
router.register("stocks", StockViewSet)

urlpatterns = [
    ] + router.urls