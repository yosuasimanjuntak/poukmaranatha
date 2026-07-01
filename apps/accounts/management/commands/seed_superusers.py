"""Idempotent superuser seed for poukmaranatha.

Creates the two production superusers `aamsa` and `yosua` with passwords from
environment variables. Safe to run repeatedly — existing users get their
password and role updated; missing users are created.

Used during fresh production install (see DEPLOYMENT.md).
"""

from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import AccountRole

User = get_user_model()


SEED_USERS = [
    {
        "username": "aamsa",
        "full_name": "aamsa",
        "password_env": "DJANGO_SUPERUSER_AAMSA_PASSWORD",
    },
    {
        "username": "yosua",
        "full_name": "yosua",
        "password_env": "DJANGO_SUPERUSER_YOSUA_PASSWORD",
    },
]


class Command(BaseCommand):
    help = "Create or update the two seeded superusers (aamsa, yosua)."

    def handle(self, *args, **options):
        for spec in SEED_USERS:
            username = spec["username"]
            password = os.environ.get(spec["password_env"])
            if not password:
                self.stderr.write(
                    self.style.ERROR(
                        f"skipped {username}: env var {spec['password_env']} is not set"
                    )
                )
                continue

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "full_name": spec["full_name"],
                    "account_role": AccountRole.SUPERUSER,
                },
            )

            # Always reset password and role so re-running fixes drift.
            user.full_name = user.full_name or spec["full_name"]
            user.account_role = AccountRole.SUPERUSER
            user.set_password(password)
            user.save()  # User.save() derives is_superuser/is_staff from account_role

            verb = "created" if created else "updated"
            self.stdout.write(
                self.style.SUCCESS(f"{verb} superuser '{username}' (account_role=superuser)")
            )
