"""Bulk-import users from a CSV file.

Usage:
    python manage.py import_users users.csv
    python manage.py import_users users.csv --dry-run

CSV columns (header row required):
    full_name     – display name (required)
    username      – login name; auto-derived from full_name if blank
    password      – initial password; defaults to username if blank
    account_role  – superuser / admin / viewer  (default: viewer)
    language      – id / en  (default: id)
    user_roles    – pipe-separated role names, e.g. "Worship Leader|Drum"
                    Roles that don't exist yet are created automatically.

Running the command a second time is safe: existing users get their
roles updated but their password is NOT overwritten unless --reset-passwords
is passed.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import AccountRole
from ministry.models import UserRole

User = get_user_model()

VALID_ROLES = {r.value for r in AccountRole}
VALID_LANGUAGES = {"id", "en"}


def slugify_username(full_name: str) -> str:
    """Derive a login username from a full name."""
    cleaned = full_name.lower().strip()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")
    return cleaned or "user"


class Command(BaseCommand):
    help = "Bulk-import users from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_file", help="Path to the CSV file")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and preview changes without writing to the database",
        )
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Overwrite passwords for existing users",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_file"])
        if not csv_path.exists():
            raise CommandError(f"File not found: {csv_path}")

        dry_run = options["dry_run"]
        reset_passwords = options["reset_passwords"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be saved.\n"))

        rows = self._parse(csv_path)
        if not rows:
            raise CommandError("CSV is empty or has no data rows.")

        created = updated = skipped = 0

        with transaction.atomic():
            for i, row in enumerate(rows, start=2):  # row 1 = header
                result = self._process_row(row, i, dry_run, reset_passwords)
                if result == "created":
                    created += 1
                elif result == "updated":
                    updated += 1
                else:
                    skipped += 1

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {created} created, {updated} updated, {skipped} skipped"
                + (" (dry run — nothing saved)" if dry_run else "")
            )
        )

    def _parse(self, path: Path) -> list[dict]:
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            required = {"full_name"}
            if not required.issubset({c.strip().lower() for c in (reader.fieldnames or [])}):
                raise CommandError(
                    f"CSV is missing required column(s): {required - set(reader.fieldnames or [])}"
                )
            return [
                {k.strip().lower(): v.strip() for k, v in row.items()}
                for row in reader
                if any(v.strip() for v in row.values())
            ]

    def _process_row(self, row: dict, line: int, dry_run: bool, reset_passwords: bool) -> str:
        full_name = row.get("full_name", "").strip()
        if not full_name:
            self.stderr.write(f"  line {line}: skipped — full_name is blank")
            return "skipped"

        username = row.get("username", "").strip() or slugify_username(full_name)
        password = row.get("password", "").strip() or username

        account_role_raw = row.get("account_role", "").strip().lower() or "viewer"
        if account_role_raw not in VALID_ROLES:
            self.stderr.write(
                f"  line {line}: skipped '{username}' — invalid account_role '{account_role_raw}'"
            )
            return "skipped"
        account_role = account_role_raw

        language = row.get("language", "").strip().lower() or "id"
        if language not in VALID_LANGUAGES:
            self.stderr.write(
                f"  line {line}: skipped '{username}' — invalid language '{language}'"
            )
            return "skipped"

        role_names = [
            r.strip() for r in row.get("user_roles", "").split("|") if r.strip()
        ]

        user_roles = []
        for name in role_names:
            if not dry_run:
                role, _ = UserRole.objects.get_or_create(name=name)
            else:
                role = UserRole.objects.filter(name=name).first()
                if not role:
                    self.stdout.write(f"    [dry-run] would create UserRole '{name}'")
                    continue
            user_roles.append(role)

        existing = User.objects.filter(username=username).first()

        if existing:
            changed = False
            if existing.full_name != full_name:
                existing.full_name = full_name
                changed = True
            if existing.account_role != account_role:
                existing.account_role = account_role
                changed = True
            if existing.language != language:
                existing.language = language
                changed = True
            if reset_passwords:
                existing.set_password(password)
                changed = True
            if not dry_run:
                if changed:
                    existing.save()
                existing.user_roles.set(user_roles)
            self.stdout.write(f"  updated  '{username}' ({full_name}) roles={role_names or '-'}")
            return "updated"
        else:
            if not dry_run:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    full_name=full_name,
                    account_role=account_role,
                    language=language,
                )
                user.user_roles.set(user_roles)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  created  '{username}' ({full_name}) roles={role_names or '-'}"
                )
            )
            return "created"
