from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import AccountRole


def is_superuser_role(user):
    return user.is_authenticated and user.account_role == AccountRole.SUPERUSER


def is_admin_or_above(user):
    return user.is_authenticated and user.account_role in {
        AccountRole.SUPERUSER,
        AccountRole.ADMIN,
    }


class AdminOrAboveRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return is_admin_or_above(self.request.user)


class SuperuserRoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return is_superuser_role(self.request.user)
