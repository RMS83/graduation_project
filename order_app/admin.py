from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import User, Vendor, Purchaser


class AddUserForm(forms.ModelForm):
    """
    New User Form. Requires password confirmation.
    """
    password1 = forms.CharField(
        label='Password', widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label='Confirm password', widget=forms.PasswordInput
    )

    phone = forms.CharField(
        label='Phone', widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UpdateUserForm(forms.ModelForm):
    """
    Update User Form. Doesn't allow changing password in the Admin.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            'email', 'password', 'first_name', 'last_name', 'is_active',
            'is_staff',
        )

    def clean_password(self):
        # Password can't be changed in the admin
        return self.initial["password"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UpdateUserForm
    add_form = AddUserForm

    list_display = ('id', 'email', 'first_name', 'last_name', 'is_staff', 'type')
    list_filter = ('is_staff',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name',)}),
        ('Разрешения', {'fields': ('is_active', 'is_staff')}),
        ('Тип пользователя', {'fields': ('type',)}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email', 'first_name', 'last_name', 'password1',
                    'password2', 'type'
                )
            }
        ),
    )
    search_fields = ('email', 'first_name', 'last_name', 'type',)
    ordering = ('email', 'first_name', 'last_name')
    filter_horizontal = ()
    # inlines = (ShopInline,)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor_name', 'vendor_phone', 'accepting_orders', 'vendor_address')
    list_filter = ('accepting_orders',)
    fieldsets = (
        (None, {'fields': ('user', 'vendor_name')}),
        ('Вкл./Выкл. продажи', {'fields': ('accepting_orders',)}),
        ('Контакты', {'fields': ('vendor_phone', 'vendor_address')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'user', 'vendor_name', 'vendor_phone', 'accepting_orders', 'vendor_address'
                )
            }
        ),
    )
    search_fields = ('user', 'vendor_name')
    ordering = ('user', 'accepting_orders')
    filter_horizontal = ()


@admin.register(Purchaser)
class PurchaserAdmin(admin.ModelAdmin):
    list_display = ('id', 'purchaser_name', 'purchaser_phone', 'purchaser_address')
    list_filter = ('purchaser_name',)
    fieldsets = (
        (None, {'fields': ('user', 'purchaser_name')}),
        ('Контакты', {'fields': ('purchaser_phone', 'purchaser_address')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'user', 'purchaser_name', 'purchaser_phone', 'purchaser_address'
                )
            }
        ),
    )
    search_fields = ('user', 'purchaser_name')
    ordering = ('id',)
    filter_horizontal = ()
