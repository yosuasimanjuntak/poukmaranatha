from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "full_name",
        "email",
        "account_role",
        "is_active",
        "last_login",
    )
    list_filter = ("account_role", "is_active", "user_roles")
    search_fields = ("username", "full_name", "email")
    filter_horizontal = ("user_roles", "groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Profile"),
            {"fields": ("full_name", "email", "photo", "language")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "account_role",
                    "user_roles",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "full_name",
                    "email",
                    "password1",
                    "password2",
                    "account_role",
                ),
            },
        ),
    )
