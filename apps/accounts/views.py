from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from .forms import ProfileForm, UserCreationForm, UserUpdateForm
from .permissions import is_admin_or_above

User = get_user_model()


@login_required
def manage_index(request: HttpRequest) -> HttpResponse:
    if not is_admin_or_above(request.user):
        return HttpResponse(status=403)
    counts = {
        "users": User.objects.count(),
    }
    return render(request, "accounts/manage_index.html", {"counts": counts})


@login_required
def user_list(request: HttpRequest) -> HttpResponse:
    if not is_admin_or_above(request.user):
        return HttpResponse(status=403)
    q = (request.GET.get("q") or "").strip()
    qs = User.objects.all().order_by("full_name", "username")
    if q:
        qs = (
            qs.filter(username__icontains=q)
            | qs.filter(full_name__icontains=q)
            | qs.filter(email__icontains=q)
        )
    role_filter = request.GET.get("role") or ""
    if role_filter:
        qs = qs.filter(user_roles__id=role_filter).distinct()
    return render(
        request,
        "accounts/user_list.html",
        {"users": qs[:200], "q": q, "selected_role": role_filter},
    )


@login_required
def user_create(request: HttpRequest) -> HttpResponse:
    if not is_admin_or_above(request.user):
        return HttpResponse(status=403)
    if request.method == "POST":
        form = UserCreationForm(request.POST, request.FILES, requestor=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("User %(name)s created.") % {"name": user.display_name})
            return redirect("accounts:user_list")
    else:
        form = UserCreationForm(requestor=request.user)
    return render(request, "accounts/user_form.html", {"form": form, "mode": "create"})


@login_required
def user_edit(request: HttpRequest, pk: int) -> HttpResponse:
    if not is_admin_or_above(request.user):
        return HttpResponse(status=403)
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, request.FILES, instance=user, requestor=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("User updated."))
            return redirect("accounts:user_list")
    else:
        form = UserUpdateForm(instance=user, requestor=request.user)
    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "mode": "edit", "user_obj": user},
    )


@login_required
def user_delete(request: HttpRequest, pk: int) -> HttpResponse:
    if not is_admin_or_above(request.user):
        return HttpResponse(status=403)
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, _("You cannot delete your own account."))
        return redirect("accounts:user_list")
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, _("Only Superuser can delete another Superuser."))
        return redirect("accounts:user_list")
    if request.method == "POST":
        name = user.display_name
        user.delete()
        messages.success(request, _("Deleted user %(name)s.") % {"name": name})
        return redirect("accounts:user_list")
    return render(request, "accounts/user_confirm_delete.html", {"user_obj": user})


@login_required
def profile_edit(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated."))
            return redirect("accounts:profile_edit")
    else:
        form = ProfileForm(instance=request.user)
    pw_form = PasswordChangeForm(user=request.user)
    return render(
        request,
        "accounts/profile_edit.html",
        {"form": form, "pw_form": pw_form},
    )


@login_required
def profile_password(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return redirect("accounts:profile_edit")
    form = PasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
        form.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, _("Password changed."))
        return redirect("accounts:profile_edit")
    profile_form = ProfileForm(instance=request.user)
    return render(
        request,
        "accounts/profile_edit.html",
        {"form": profile_form, "pw_form": form},
    )
