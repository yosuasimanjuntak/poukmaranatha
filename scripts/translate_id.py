"""One-off helper to fill Indonesian translations into locale/id/LC_MESSAGES/django.po.

Run from project root: python scripts/translate_id.py
After running, run: python manage.py compilemessages
"""

from pathlib import Path

TRANSLATIONS = {
    # accounts
    "Profile": "Profil",
    "Permissions": "Izin",
    "Important dates": "Tanggal penting",
    "account role": "peran akun",
    "Superuser": "Super-admin",
    "Admin": "Admin",
    "Viewer": "Pengamat",
    "full name": "nama lengkap",
    "photo": "foto",
    "preferred language": "bahasa pilihan",
    "ministry roles": "peran pelayanan",
    "user": "pengguna",
    "users": "pengguna",
    "User %(name)s created.": "Pengguna %(name)s dibuat.",
    "User updated.": "Pengguna diperbarui.",
    "You cannot delete your own account.": "Anda tidak bisa menghapus akun Anda sendiri.",
    "Only Superuser can delete another Superuser.": "Hanya Super-admin yang bisa menghapus Super-admin lain.",
    "Deleted user %(name)s.": "Pengguna %(name)s dihapus.",
    "Profile updated.": "Profil diperbarui.",
    "Password changed.": "Kata sandi diubah.",
    # ministry forms / models
    "Duration (minutes)": "Durasi (menit)",
    "(auto from start date)": "(otomatis dari tanggal mulai)",
    "Monday": "Senin",
    "Tuesday": "Selasa",
    "Wednesday": "Rabu",
    "Thursday": "Kamis",
    "Friday": "Jumat",
    "Saturday": "Sabtu",
    "Sunday": "Minggu",
    "End date must be on or after start date.": "Tanggal selesai harus pada atau setelah tanggal mulai.",
    "name": "nama",
    "name (English)": "nama (Inggris)",
    "description": "deskripsi",
    "active": "aktif",
    "display order": "urutan tampilan",
    "pelayanan": "pelayanan",
    "ministry role": "peran pelayanan",
    "count": "jumlah",
    "role slot template": "templat slot peran",
    "role slot templates": "templat slot peran",
    "Daily": "Harian",
    "Weekly": "Mingguan",
    "Monthly": "Bulanan",
    "frequency": "frekuensi",
    "start date": "tanggal mulai",
    "end date": "tanggal selesai",
    "start time": "waktu mulai",
    "duration (minutes)": "durasi (menit)",
    "weekday": "hari dalam minggu",
    "day of month": "tanggal dalam bulan",
    "location": "lokasi",
    "notes": "catatan",
    "recurrence rule": "aturan pengulangan",
    "recurrence rules": "aturan pengulangan",
    "start at": "mulai pada",
    "end at": "berakhir pada",
    "cancelled": "dibatalkan",
    "schedule": "jadwal",
    "schedules": "jadwal",
    "slot index": "indeks slot",
    "assignment": "penugasan",
    "assignments": "penugasan",
    "Created %(count)d schedule instances.": "Berhasil membuat %(count)d jadwal.",
    "Schedule created.": "Jadwal dibuat.",
    "Schedule updated.": "Jadwal diperbarui.",
    "Pelayanan saved.": "Pelayanan disimpan.",
    "Role slot added.": "Slot peran ditambahkan.",
    "Could not add role slot.": "Tidak dapat menambah slot peran.",
    "Role slot removed.": "Slot peran dihapus.",
    "Slot updated.": "Slot diperbarui.",
    "Ministry role saved.": "Peran pelayanan disimpan.",
    # navigation / manage_index
    "Manage": "Kelola",
    "Management": "Manajemen",
    "Users": "Pengguna",
    "Manage accounts and ministry roles": "Kelola akun dan peran pelayanan",
    "Schedules": "Jadwal",
    "Create new (one-off or recurring)": "Buat baru (sekali atau berulang)",
    "Pelayanan": "Pelayanan",
    "Categories and role lineups": "Kategori dan susunan peran",
    "Ministry roles": "Peran Pelayanan",
    "Worship Leader, Drum, Singer, etc.": "Worship Leader, Drum, Singer, dsb.",
    "Django admin": "Admin Django",
    "Raw data and recurrences": "Data mentah dan pengulangan",
    # profile
    "Edit profile": "Edit profil",
    "Save profile": "Simpan profil",
    "Change password": "Ubah kata sandi",
    "Update password": "Perbarui kata sandi",
    "Log out": "Keluar",
    # users
    "Delete user": "Hapus pengguna",
    "Delete this user?": "Hapus pengguna ini?",
    "This will permanently delete <strong>%(name)s</strong>. This action cannot be undone.": "Ini akan menghapus <strong>%(name)s</strong> secara permanen. Tindakan ini tidak dapat dibatalkan.",
    "Yes, delete": "Ya, hapus",
    "Cancel": "Batal",
    "New user": "Pengguna baru",
    "Edit user": "Edit pengguna",
    "Save": "Simpan",
    "Search by name, username, or email": "Cari berdasarkan nama, username, atau email",
    "New": "Baru",
    "Delete": "Hapus",
    "No users match.": "Tidak ada pengguna yang cocok.",
    # nav / tabs
    "Primary": "Utama",
    "Schedule": "Jadwal",
    "My Schedule": "Jadwalku",
    # assignment row / picker
    "Empty": "Kosong",
    "Change": "Ubah",
    "Assign": "Tugaskan",
    "Clear": "Kosongkan",
    "All": "Semua",
    "Role": "Peran",
    "Show": "Tampilkan",
    "Upcoming only": "Mendatang saja",
    "All including past": "Semua termasuk yang lalu",
    "Clear filters": "Hapus filter",
    "slot": "slot",
    "No schedules match your filters.": "Tidak ada jadwal yang cocok dengan filter.",
    "Assign %(role)s": "Tugaskan %(role)s",
    "Search": "Cari",
    "No users found with this ministry role.": "Tidak ada pengguna dengan peran pelayanan ini.",
    "My assignments": "Tugas saya",
    "Where you are scheduled to serve.": "Di mana Anda dijadwalkan melayani.",
    "Hide past": "Sembunyikan yang lalu",
    "Show past": "Tampilkan yang lalu",
    "You have no assignments.": "Anda belum memiliki tugas.",
    # pelayanan / userrole CRUD
    "New pelayanan": "Pelayanan baru",
    "Edit pelayanan": "Edit pelayanan",
    "role slot": "slot peran",
    "inactive": "tidak aktif",
    "Edit": "Edit",
    "No pelayanan yet.": "Belum ada pelayanan.",
    "Role lineup": "Susunan peran",
    "When a schedule is created for this pelayanan, these slots will be auto-created.": "Saat jadwal dibuat untuk pelayanan ini, slot-slot ini akan otomatis dibuat.",
    "Edit pelayanan details": "Edit detail pelayanan",
    "Remove": "Hapus",
    "No slots yet. Add one below.": "Belum ada slot. Tambahkan di bawah.",
    "Add slot": "Tambah slot",
    "Count": "Jumlah",
    "Order": "Urutan",
    "Add": "Tambah",
    "Edit (admin)": "Edit (admin)",
    "No role slots configured for this Pelayanan.": "Belum ada slot peran untuk pelayanan ini.",
    "Edit schedule": "Edit jadwal",
    "New schedule": "Jadwal baru",
    "One-off": "Sekali",
    "Recurring": "Berulang",
    "New ministry role": "Peran pelayanan baru",
    "Edit ministry role": "Edit peran pelayanan",
    "No ministry roles yet.": "Belum ada peran pelayanan.",
    # login
    "Log in": "Masuk",
    "Invalid username or password.": "Username atau kata sandi salah.",
    "Username": "Username",
    "Password": "Kata sandi",
}


def patch(po_path: Path, translations: dict[str, str]) -> int:
    """Replace empty msgstr "" lines with the matching translation."""
    lines = po_path.read_text(encoding="utf-8").splitlines(keepends=False)
    out: list[str] = []
    i = 0
    matched = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        # Track msgid possibly multi-line
        if line.startswith("msgid ") and i + 1 < len(lines):
            # Collect msgid value (handle continuation lines)
            value, j = _collect(lines, i)
            # Skip msgid_plural if present
            k = j
            if k < len(lines) and lines[k].startswith("msgid_plural"):
                _, k = _collect(lines, k)
            # Look for msgstr ""
            if k < len(lines) and lines[k] == 'msgstr ""':
                if value in translations:
                    # Append all the in-between lines we already added... wait no
                    # Re-emit: continue from where we are, but replace msgstr line
                    # Append remaining msgid continuation lines
                    while i + 1 < j:
                        i += 1
                        out.append(lines[i])
                    # Append msgstr replaced
                    i = k
                    out.append(f'msgstr "{translations[value]}"')
                    matched += 1
        i += 1
    po_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return matched


def _collect(lines: list[str], i: int) -> tuple[str, int]:
    """Collect a quoted string value (possibly across continuation lines).

    Returns (concatenated_value, next_index_after_value).
    """
    parts: list[str] = []
    # First line: msgid "..." or msgid_plural "..."
    first = lines[i]
    quoted = first.split(" ", 1)[1] if " " in first else ""
    parts.append(_unquote(quoted))
    j = i + 1
    while j < len(lines) and lines[j].startswith('"'):
        parts.append(_unquote(lines[j]))
        j += 1
    return "".join(parts), j


def _unquote(s: str) -> str:
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s.encode("utf-8").decode("unicode_escape")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    po = project_root / "locale" / "id" / "LC_MESSAGES" / "django.po"
    n = patch(po, TRANSLATIONS)
    print(f"Filled {n} translations into {po}")
