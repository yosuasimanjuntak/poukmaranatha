def account_role(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {
            "is_admin_or_above": False,
            "is_superuser_role": False,
        }
    return {
        "is_admin_or_above": user.is_admin_or_above,
        "is_superuser_role": user.account_role == "superuser",
    }
