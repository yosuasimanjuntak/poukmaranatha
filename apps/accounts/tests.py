import pytest
from accounts.models import AccountRole
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.fixture
def viewer(db):
    return User.objects.create_user(
        username="viewer1", password="x", account_role=AccountRole.VIEWER
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(username="admin1", password="x", account_role=AccountRole.ADMIN)


@pytest.fixture
def superuser_account(db):
    return User.objects.create_user(
        username="super1", password="x", account_role=AccountRole.SUPERUSER
    )


def test_login_page_returns_200(db, client: Client) -> None:
    response = client.get(reverse("login"))
    assert response.status_code == 200


def test_account_role_mirrors_to_django_flags(viewer, admin_user, superuser_account):
    assert viewer.is_staff is False and viewer.is_superuser is False
    assert admin_user.is_staff is True and admin_user.is_superuser is False
    assert superuser_account.is_staff is True and superuser_account.is_superuser is True


def test_viewer_cannot_reach_manage(client, viewer):
    client.force_login(viewer)
    response = client.get(reverse("accounts:manage_index"))
    assert response.status_code == 403


def test_admin_can_reach_manage(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("accounts:manage_index"))
    assert response.status_code == 200


def test_admin_cannot_promote_to_superuser(client, admin_user):
    """The role choice list should not include SUPERUSER for non-superuser requestors."""
    from accounts.forms import UserCreationForm

    form = UserCreationForm(requestor=admin_user)
    role_choices = [c[0] for c in form.fields["account_role"].choices]
    assert AccountRole.SUPERUSER not in role_choices
    assert AccountRole.ADMIN in role_choices
    assert AccountRole.VIEWER in role_choices


def test_superuser_can_promote_to_superuser(superuser_account):
    from accounts.forms import UserCreationForm

    form = UserCreationForm(requestor=superuser_account)
    role_choices = [c[0] for c in form.fields["account_role"].choices]
    assert AccountRole.SUPERUSER in role_choices


def test_profile_form_does_not_expose_account_role(viewer):
    from accounts.forms import ProfileForm

    form = ProfileForm(instance=viewer)
    assert "account_role" not in form.fields
    assert "user_roles" not in form.fields


def test_user_can_self_edit_profile(client, viewer, tmp_path):
    client.force_login(viewer)
    response = client.post(
        reverse("accounts:profile_edit"),
        data={"full_name": "Budi Santoso", "email": "", "language": "id"},
    )
    assert response.status_code == 302
    viewer.refresh_from_db()
    assert viewer.full_name == "Budi Santoso"
