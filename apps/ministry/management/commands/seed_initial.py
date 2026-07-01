"""Seed initial Pelayanan and UserRole data from the church reference list.

Idempotent: re-running won't create duplicates. Pass --with-templates to also
add a sensible default role-slot lineup for each Pelayanan; admin can adjust
those later in /manage/pelayanan/<id>/.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from ministry.models import Pelayanan, PelayananRoleSlot, UserRole

PELAYANAN = [
    # (name, name_en, order)
    ("Umum", "General Service", 10),
    ("Sekolah Minggu", "Sunday School", 20),
    ("Pemuda", "Youth", 30),
    ("Wanita", "Women", 40),
    ("Lansia", "Elderly", 50),
    ("Remaja", "Teen", 60),
]

USER_ROLES = [
    # (name, name_en, order)
    ("Pelayan Firman", "Preacher", 10),
    ("Pendamping", "Co-host", 20),
    ("Worship Leader", "Worship Leader", 30),
    ("Singer", "Singer", 40),
    ("Keyboard Leader", "Keyboard Leader", 50),
    ("Keyboard Filler", "Keyboard Filler", 60),
    ("Gitar", "Guitar", 70),
    ("Bass", "Bass", 80),
    ("Drum", "Drum", 90),
    ("Kajon", "Cajon", 100),
    ("Tambourine", "Tambourine", 110),
    ("Multimedia", "Multimedia", 120),
    ("Warta", "Announcements", 130),
    ("Kolekte", "Collection", 140),
    ("Kolekte & Penerima Tamu", "Collection & Usher", 150),
]

# Default lineup per Pelayanan: list of (user_role_name, count, order)
# Tweakable later in the UI.
DEFAULT_LINEUP = {
    "Umum": [
        ("Pelayan Firman", 1, 10),
        ("Pendamping", 1, 20),
        ("Worship Leader", 1, 30),
        ("Singer", 3, 40),
        ("Keyboard Leader", 1, 50),
        ("Gitar", 1, 60),
        ("Bass", 1, 70),
        ("Drum", 1, 80),
        ("Multimedia", 1, 90),
        ("Warta", 1, 100),
        ("Kolekte & Penerima Tamu", 2, 110),
    ],
    "Sekolah Minggu": [
        ("Pelayan Firman", 1, 10),
        ("Pendamping", 1, 20),
        ("Multimedia", 1, 30),
    ],
    "Pemuda": [
        ("Pelayan Firman", 1, 10),
        ("Worship Leader", 1, 20),
        ("Singer", 2, 30),
        ("Keyboard Filler", 1, 40),
        ("Gitar", 1, 50),
        ("Drum", 1, 60),
        ("Multimedia", 1, 70),
    ],
    "Wanita": [
        ("Pelayan Firman", 1, 10),
        ("Worship Leader", 1, 20),
        ("Singer", 2, 30),
        ("Keyboard Filler", 1, 40),
        ("Multimedia", 1, 50),
    ],
    "Lansia": [
        ("Pelayan Firman", 1, 10),
        ("Worship Leader", 1, 20),
        ("Keyboard Filler", 1, 30),
    ],
    "Remaja": [
        ("Pelayan Firman", 1, 10),
        ("Worship Leader", 1, 20),
        ("Singer", 2, 30),
        ("Gitar", 1, 40),
        ("Drum", 1, 50),
        ("Multimedia", 1, 60),
    ],
}


class Command(BaseCommand):
    help = "Seed initial Pelayanan and UserRole data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-templates",
            action="store_true",
            help="Also create default PelayananRoleSlot lineups.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        for name, name_en, order in USER_ROLES:
            UserRole.objects.update_or_create(
                name=name,
                defaults={"name_en": name_en, "order": order, "is_active": True},
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(USER_ROLES)} user roles"))

        for name, name_en, order in PELAYANAN:
            Pelayanan.objects.update_or_create(
                name=name,
                defaults={"name_en": name_en, "order": order, "is_active": True},
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(PELAYANAN)} pelayanan"))

        if options["with_templates"]:
            roles_by_name = {r.name: r for r in UserRole.objects.all()}
            slot_count = 0
            for pelayanan_name, lineup in DEFAULT_LINEUP.items():
                pelayanan = Pelayanan.objects.get(name=pelayanan_name)
                for role_name, count, order in lineup:
                    role = roles_by_name[role_name]
                    PelayananRoleSlot.objects.update_or_create(
                        pelayanan=pelayanan,
                        user_role=role,
                        defaults={"count": count, "order": order},
                    )
                    slot_count += 1
            self.stdout.write(self.style.SUCCESS(f"Seeded {slot_count} role slot templates"))
