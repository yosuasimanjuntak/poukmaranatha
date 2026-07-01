from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class AccountRole(models.TextChoices):
    SUPERUSER = "superuser", _("Superuser")
    ADMIN = "admin", _("Admin")
    VIEWER = "viewer", _("Viewer")


class User(AbstractUser):
    full_name = models.CharField(_("full name"), max_length=150, blank=True)
    photo = models.ImageField(_("photo"), upload_to="profile_photos/", blank=True, null=True)
    account_role = models.CharField(
        _("account role"),
        max_length=16,
        choices=AccountRole.choices,
        default=AccountRole.VIEWER,
    )
    language = models.CharField(
        _("preferred language"),
        max_length=8,
        default="id",
    )
    pelayanan_categories = models.ManyToManyField(
        "ministry.Pelayanan",
        blank=True,
        related_name="eligible_users",
        verbose_name=_("service categories"),
    )
    user_roles = models.ManyToManyField(
        "ministry.UserRole",
        blank=True,
        related_name="users",
        verbose_name=_("ministry roles"),
    )

    class Meta(AbstractUser.Meta):
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def save(self, *args, **kwargs):
        if self.account_role == AccountRole.SUPERUSER:
            self.is_superuser = True
            self.is_staff = True
        elif self.account_role == AccountRole.ADMIN:
            self.is_superuser = False
            self.is_staff = True
        else:
            self.is_superuser = False
            self.is_staff = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name or self.username

    @property
    def display_name(self):
        return self.full_name or self.username

    @property
    def is_admin_or_above(self):
        return self.account_role in {AccountRole.SUPERUSER, AccountRole.ADMIN}
