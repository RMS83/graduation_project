from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver

from .models import User, Vendor, Purchaser, ShoppingCart
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken



@receiver(post_save, sender=User)
def create_user_vendor_purchaser(sender, instance, created, **kwargs):

    if created:
        if instance.is_superuser:
            User.objects.create(user=instance)
        if instance.type == 'vendor':
            Vendor.objects.create(user=instance)
        else:
            Purchaser.objects.create(user=instance)

@receiver(post_save, sender=Purchaser)
def create_shopping_cart(sender, instance, created, **kwargs):

    if created:
        print(instance)
        ShoppingCart.objects.create(purchaser=instance)


@receiver(pre_delete, sender=Vendor)
def del_user_token(sender, instance, **kwargs):
    blacklist = BlacklistedToken.objects.filter(token__user=instance.user)
    if blacklist:
        [bl_token.delete() for bl_token in blacklist]

    whitelist = OutstandingToken.objects.filter(user_id=instance.user.id)
    if whitelist:
        [wl_token.delete() for wl_token in whitelist]

@receiver(post_delete, sender=Vendor)
def del_user_token(sender, instance, **kwargs):
    User.objects.get(id=instance.user.id).delete()


@receiver(pre_delete, sender=Purchaser)
def del_user_token(sender, instance, **kwargs):
    blacklist = BlacklistedToken.objects.filter(token__user=instance.user)
    if blacklist:
        [bl_token.delete() for bl_token in blacklist]

    whitelist = OutstandingToken.objects.filter(user_id=instance.user.id)
    if whitelist:
        [wl_token.delete() for wl_token in whitelist]

@receiver(post_delete, sender=Purchaser)
def del_user_token(sender, instance, **kwargs):
    User.objects.get(id=instance.user.id).delete()
