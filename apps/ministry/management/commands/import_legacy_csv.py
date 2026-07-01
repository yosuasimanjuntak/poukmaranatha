"""Import legacy CSV data into the new system.

Expected files in the given directory:
  worship_*.csv            → Pelayanan
  _role__*.csv             → UserRole
  person_*.csv             → User accounts
  person_role_*.csv        → User.user_roles M2M + PelayananRoleSlot templates
  schedule_assignment_*.csv→ Schedule + Assignment
  kolekte_*.csv            → Kolekte

Usage:
    python manage.py import_legacy_csv csv/
    python manage.py import_legacy_csv csv/ --dry-run
"""

from __future__ import annotations

import csv
import re
from datetime import datetime, time
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from ministry.models import (
    Assignment,
    Kolekte,
    Pelayanan,
    PelayananRoleSlot,
    Schedule,
    UserRole,
)

User = get_user_model()

DEFAULT_SERVICE_TIME = time(8, 0)


def _read(directory: Path, prefix: str) -> list[dict]:
    # Match only files whose name starts exactly with prefix followed by a digit
    # (timestamp-based filenames), to avoid e.g. "person_" matching "person_role_".
    matches = sorted(p for p in directory.glob(f"{prefix}*.csv")
                     if p.name[len(prefix):len(prefix)+1].isdigit())
    if not matches:
        raise CommandError(f"No file matching '{prefix}<timestamp>.csv' in {directory}")
    path = matches[-1]
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _slugify(name: str) -> str:
    cleaned = name.lower().strip()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")
    return cleaned or "user"


class Command(BaseCommand):
    help = "Import legacy CSV exports into the new system."

    def add_arguments(self, parser):
        parser.add_argument("csv_dir", help="Directory containing the CSV files")
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        directory = Path(options["csv_dir"])
        if not directory.is_dir():
            raise CommandError(f"Not a directory: {directory}")

        dry = options["dry_run"]
        if dry:
            self.stdout.write(self.style.WARNING("DRY RUN — nothing will be saved.\n"))

        worship_rows = _read(directory, "worship_")
        role_rows = _read(directory, "_role__")
        person_rows = _read(directory, "person_")
        person_role_rows = _read(directory, "person_role_")
        assignment_rows = _read(directory, "schedule_assignment_")
        kolekte_rows = _read(directory, "kolekte_")

        # -- 1. Pelayanan -------------------------------------------------
        pelayanan_map: dict[str, Pelayanan] = {}
        for r in worship_rows:
            name = r["name"].strip()
            if not dry:
                obj, _ = Pelayanan.objects.update_or_create(
                    name=name, defaults={"is_active": True}
                )
            else:
                obj = Pelayanan.objects.filter(name=name).first()
            if obj:
                pelayanan_map[r["id"]] = obj
        self.stdout.write(self.style.SUCCESS(f"  Pelayanan: {len(worship_rows)} processed"))

        # -- 2. UserRole --------------------------------------------------
        role_map: dict[str, UserRole] = {}
        for r in role_rows:
            name = r["name"].strip()
            if not dry:
                obj, _ = UserRole.objects.update_or_create(
                    name=name, defaults={"is_active": True}
                )
            else:
                obj = UserRole.objects.filter(name=name).first()
            if obj:
                role_map[r["id"]] = obj
        self.stdout.write(self.style.SUCCESS(f"  UserRole:  {len(role_rows)} processed"))

        # -- 3. Users (persons) -------------------------------------------
        person_map: dict[str, User] = {}
        used_usernames: set[str] = set(User.objects.values_list("username", flat=True))
        created_users = 0
        for r in person_rows:
            full_name = r["name"].strip()
            base = _slugify(full_name)
            username = base
            suffix = 2
            while username in used_usernames:
                username = f"{base}_{suffix}"
                suffix += 1
            used_usernames.add(username)

            existing = User.objects.filter(full_name=full_name).first()
            if existing:
                person_map[r["id"]] = existing
                continue

            if not dry:
                user = User.objects.create_user(
                    username=username,
                    password=username,
                    full_name=full_name,
                )
                person_map[r["id"]] = user
                created_users += 1
        self.stdout.write(self.style.SUCCESS(f"  Users:     {created_users} created, {len(person_rows) - created_users} already existed"))

        # -- 4. User roles M2M + pelayanan_categories + PelayananRoleSlot --
        seen_user_roles: set[tuple[str, str]] = set()
        seen_pelayanan_cats: set[tuple[str, str]] = set()
        seen_slots: set[tuple[str, str]] = set()
        for r in person_role_rows:
            pid, rid, wid = r["person_id"], r["role_id"], r["worship_id"]

            # user → role M2M (per unique person+role pair)
            key_ur = (pid, rid)
            if key_ur not in seen_user_roles:
                seen_user_roles.add(key_ur)
                user = person_map.get(pid)
                role = role_map.get(rid)
                if user and role and not dry:
                    user.user_roles.add(role)

            # user → pelayanan_categories M2M (per unique person+worship pair)
            key_pc = (pid, wid)
            if key_pc not in seen_pelayanan_cats:
                seen_pelayanan_cats.add(key_pc)
                user = person_map.get(pid)
                pelayanan = pelayanan_map.get(wid)
                if user and pelayanan and not dry:
                    user.pelayanan_categories.add(pelayanan)

            # Pelayanan role slot template (per unique role+worship pair)
            key_slot = (rid, wid)
            if key_slot not in seen_slots:
                seen_slots.add(key_slot)
                pelayanan = pelayanan_map.get(wid)
                role = role_map.get(rid)
                if pelayanan and role and not dry:
                    PelayananRoleSlot.objects.get_or_create(
                        pelayanan=pelayanan,
                        user_role=role,
                        defaults={"count": 1},
                    )

        self.stdout.write(self.style.SUCCESS(
            f"  UserRole M2M: {len(seen_user_roles)} pairs, "
            f"Pelayanan categories: {len(seen_pelayanan_cats)} pairs, "
            f"PelayananRoleSlot: {len(seen_slots)} templates"
        ))

        # -- 5. Schedules + Assignments -----------------------------------
        schedule_map: dict[tuple[str, str], Schedule] = {}
        created_schedules = created_assignments = 0

        for r in assignment_rows:
            pid = r["person_id"]
            rid = r["role_id"]
            wid = r["worship_id"]
            date_str = (r.get("date") or "").strip()
            category = (r.get("category") or "").strip()

            if not date_str:
                continue
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            pelayanan = pelayanan_map.get(wid)
            role = role_map.get(rid)
            user = person_map.get(pid)
            if not pelayanan or not role:
                continue

            key = (wid, date_str)
            schedule = schedule_map.get(key)
            if schedule is None:
                naive_dt = datetime.combine(date, DEFAULT_SERVICE_TIME)
                aware_dt = timezone.make_aware(naive_dt)
                if not dry:
                    schedule, created = Schedule.objects.get_or_create(
                        pelayanan=pelayanan,
                        start_at=aware_dt,
                        defaults={"notes": category},
                    )
                    if created:
                        created_schedules += 1
                        if category and not schedule.notes:
                            schedule.notes = category
                            schedule.save(update_fields=["notes"])
                else:
                    schedule = Schedule.objects.filter(
                        pelayanan=pelayanan, start_at__date=date
                    ).first()
                    created_schedules += 1
                schedule_map[key] = schedule

            if schedule and not dry:
                existing_count = Assignment.objects.filter(
                    schedule=schedule, user_role=role, user=user or None
                ).count()
                if existing_count == 0:
                    next_index = (
                        Assignment.objects.filter(schedule=schedule, user_role=role)
                        .order_by("-slot_index")
                        .values_list("slot_index", flat=True)
                        .first()
                    )
                    next_index = 0 if next_index is None else next_index + 1
                    Assignment.objects.create(
                        schedule=schedule,
                        user_role=role,
                        slot_index=next_index,
                        user=user,
                    )
                    created_assignments += 1

        self.stdout.write(self.style.SUCCESS(
            f"  Schedules: {created_schedules} created, Assignments: {created_assignments} created"
        ))

        # -- 6. Kolekte ---------------------------------------------------
        seen_kolekte: set[tuple[str, str, str]] = set()
        created_kolekte = 0

        for r in kolekte_rows:
            date_str = (r.get("date") or "").strip()
            wid = (r.get("worship_id") or "").strip()
            ktype = (r.get("type") or "Kolekte").strip()
            total_str = (r.get("total") or "0").strip()

            if not date_str or not wid:
                continue

            key = (date_str, wid, ktype)
            if key in seen_kolekte:
                continue
            seen_kolekte.add(key)

            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                total = int(float(total_str))
            except (ValueError, TypeError):
                continue

            pelayanan = pelayanan_map.get(wid)
            if not pelayanan:
                continue

            if not dry:
                naive_dt = datetime.combine(date, DEFAULT_SERVICE_TIME)
                aware_dt = timezone.make_aware(naive_dt)
                schedule = Schedule.objects.filter(
                    pelayanan=pelayanan, start_at__date=date
                ).first()
                if not schedule:
                    schedule, _ = Schedule.objects.get_or_create(
                        pelayanan=pelayanan,
                        start_at=aware_dt,
                    )
                exists = Kolekte.objects.filter(
                    schedule=schedule, type=ktype, total=total
                ).exists()
                if not exists:
                    Kolekte.objects.create(schedule=schedule, type=ktype, total=total)
                    created_kolekte += 1

        self.stdout.write(self.style.SUCCESS(f"  Kolekte:   {created_kolekte} records created"))

        if dry:
            transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            "Import complete" + (" (dry run — nothing saved)" if dry else "")
        ))
