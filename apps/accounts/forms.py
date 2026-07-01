from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.utils.translation import gettext_lazy as _
from ministry.models import Pelayanan, UserRole

from .models import AccountRole, User


class UserCreationForm(BaseUserCreationForm):
    """Form for admins/superusers to register a new user."""

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("username", "full_name", "email", "account_role", "pelayanan_categories", "user_roles")
        widgets = {
            "pelayanan_categories": forms.CheckboxSelectMultiple,
            "user_roles": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, requestor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.requestor = requestor
        self.fields["account_role"] = forms.ChoiceField(
            label=_("account role"),
            choices=self._allowed_role_choices(),
            initial=AccountRole.VIEWER,
        )
        self.fields["pelayanan_categories"].queryset = Pelayanan.objects.filter(is_active=True)
        self.fields["pelayanan_categories"].required = False
        self.fields["user_roles"].queryset = UserRole.objects.filter(is_active=True)
        self.fields["user_roles"].required = False
        self.fields["email"].required = False
        self.fields["full_name"].required = False

    def _allowed_role_choices(self):
        choices = list(AccountRole.choices)
        # Only Superuser can create another Superuser.
        if not (self.requestor and self.requestor.is_superuser):
            choices = [c for c in choices if c[0] != AccountRole.SUPERUSER]
        return choices


class UserUpdateForm(forms.ModelForm):
    """Admin/Superuser editing another user."""

    class Meta:
        model = User
        fields = (
            "username",
            "full_name",
            "email",
            "photo",
            "account_role",
            "pelayanan_categories",
            "user_roles",
            "language",
            "is_active",
        )
        widgets = {
            "pelayanan_categories": forms.CheckboxSelectMultiple,
            "user_roles": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, requestor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.requestor = requestor
        if not (requestor and requestor.is_superuser):
            self.fields["account_role"].choices = [
                c for c in AccountRole.choices if c[0] != AccountRole.SUPERUSER
            ]
        self.fields["pelayanan_categories"].queryset = Pelayanan.objects.filter(is_active=True)
        self.fields["pelayanan_categories"].required = False
        self.fields["user_roles"].queryset = UserRole.objects.filter(is_active=True)
        self.fields["user_roles"].required = False


class ProfileForm(forms.ModelForm):
    """A user editing their own profile. account_role and user_roles are NOT here."""

    class Meta:
        model = User
        fields = ("full_name", "email", "photo", "language")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = False
        self.fields["full_name"].required = False
