from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Permission class to grant permissions to user whose 'is_staff' status is True
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.is_staff

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff


class IsVendorOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'vendor' and owner them self
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.type == "vendor"

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user


class IsVendorNoOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'vendor'
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.type == "vendor"

    def has_object_permission(self, request, view, obj):
        return request.user.vendor


class IsVendorCategoryOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'vendor' and owner category
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.type == "vendor"

    def has_object_permission(self, request, view, obj):
        return request.user == obj.vendor.user


class IsVendorStockOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'vendor' and owner stock
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        if request.user.type == "vendor":
            return True
        return False

    def has_object_permission(self, request, view, obj):
        return request.user == obj.vendor.user


class IsVendorStockProductOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'vendor' and owner of the product in his stock
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        if request.user.type == "vendor":
            return True
        return False

    def has_object_permission(self, request, view, obj):
        return request.user == obj.stock.vendor.user


class IsPurchaserNoOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'purchaser'
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.type == "purchaser"

    def has_object_permission(self, request, view, obj):
        return request.user.purchaser


class IsPurchaserOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'purchaser' and owner them self
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.type == "purchaser"

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user


class IsPurchaserRetailStoreOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'purchaser' and owner retail stores
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.type == "purchaser"

    def has_object_permission(self, request, view, obj):
        return request.user == obj.purchaser.user


class IsVendorCartStockOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'vendor' and owner
    of the stock whose products are in the shopping cart
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        if request.user.type == "vendor":
            return True
        return False

    def has_object_permission(self, request, view, obj):
        for position in obj.cart_positions.all():
            if position.stock.vendor.user == request.user:
                return True
        return False


class IsPurchaserCartOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'purchaser' and owner shopping cart
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        if request.user.type == "purchaser":
            return True
        return False

    def has_object_permission(self, request, view, obj):
        return request.user == obj.purchaser.user


class IsPurchaserCartPositionOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'purchaser' and owner of position on shopping cart
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        if request.user.type == "purchaser":
            return True
        return False

    def has_object_permission(self, request, view, obj):
        return request.user == obj.shopping_cart.purchaser.user


class IsVendorStockOrderPositionOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'vendor' and owner
    of the stock whose products are in the positions of order
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        if request.user.type == "vendor":
            return True
        return False

    def has_object_permission(self, request, view, obj):
        return request.user == obj.stock.vendor.user


class IsVendorOrderStockOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'vendor' and owner
    of the stock whose products are in the order
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        if request.user.type == "vendor":
            return True
        return False

    def has_object_permission(self, request, view, obj):
        for position in obj.order_positions.all():
            if request.user == position.stock.vendor.user:
                return True
        return False


class IsPurchaserOrderStatusOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'purchaser' and owner
    of the status self order
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        if request.user.type == "purchaser":
            return True
        return False

    def has_object_permission(self, request, view, obj):
        return request.user == obj.order.purchaser.user


class IsVendorOrderStatusOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'vendor' and owner
    the status position  in the order
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        if request.user.type == "vendor":
            return True
        return False

    def has_object_permission(self, request, view, obj):
        return request.user == obj.order.order_positions.stock.vendor.user


class IsPurchaserOrderPositionOwner(BasePermission):
    """
    Permission class to grant permissions to user whose type is 'purchaser' and owner
    of positions in orders
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        if request.user.type == "purchaser":
            return True
        return False

    def has_object_permission(self, request, view, obj):
        return request.user == obj.order.purchaser.user
