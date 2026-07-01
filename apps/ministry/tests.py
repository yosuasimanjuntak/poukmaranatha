from datetime import date, time, timedelta

import pytest
from accounts.models import AccountRole
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from ministry.models import (
    Assignment,
    Pelayanan,
    PelayananRoleSlot,
    RecurrenceRule,
    Schedule,
    UserRole,
)
from ministry.services import (
    create_one_off_schedule,
    expand_recurrence,
    materialize_assignments,
)

User = get_user_model()


@pytest.fixture
def umum(db):
    return Pelayanan.objects.create(name="Umum", order=10)


@pytest.fixture
def role_wl(db):
    return UserRole.objects.create(name="Worship Leader", order=10)


@pytest.fixture
def role_singer(db):
    return UserRole.objects.create(name="Singer", order=20)


@pytest.fixture
def umum_with_lineup(db, umum, role_wl, role_singer):
    PelayananRoleSlot.objects.create(pelayanan=umum, user_role=role_wl, count=1, order=10)
    PelayananRoleSlot.objects.create(pelayanan=umum, user_role=role_singer, count=3, order=20)
    return umum


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(username="adm", password="x", account_role=AccountRole.ADMIN)


def test_materialize_assignments_creates_one_row_per_slot(umum_with_lineup):
    schedule = Schedule.objects.create(
        pelayanan=umum_with_lineup,
        start_at=timezone.now(),
    )
    materialize_assignments(schedule)
    assert Assignment.objects.filter(schedule=schedule).count() == 4
    materialize_assignments(schedule)
    assert Assignment.objects.filter(schedule=schedule).count() == 4


def test_create_one_off_schedule(umum_with_lineup):
    start = timezone.now() + timedelta(days=1)
    schedule = create_one_off_schedule(
        pelayanan=umum_with_lineup,
        start_at=start,
        duration_minutes=120,
    )
    assert schedule.start_at == start
    assert schedule.end_at == start + timedelta(minutes=120)
    assert schedule.assignments.count() == 4


def test_expand_recurrence_weekly(umum_with_lineup):
    rule = RecurrenceRule.objects.create(
        frequency=RecurrenceRule.Frequency.WEEKLY,
        pelayanan=umum_with_lineup,
        start_date=date(2026, 5, 10),
        end_date=date(2026, 5, 31),
        start_time=time(9, 0),
        weekday=6,
    )
    created = expand_recurrence(rule)
    assert len(created) == 4
    for s in created:
        assert s.assignments.count() == 4


def test_expand_recurrence_daily(umum_with_lineup):
    rule = RecurrenceRule.objects.create(
        frequency=RecurrenceRule.Frequency.DAILY,
        pelayanan=umum_with_lineup,
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 7),
        start_time=time(6, 0),
    )
    created = expand_recurrence(rule)
    assert len(created) == 7


def test_expand_recurrence_monthly(umum_with_lineup):
    rule = RecurrenceRule.objects.create(
        frequency=RecurrenceRule.Frequency.MONTHLY,
        pelayanan=umum_with_lineup,
        start_date=date(2026, 1, 15),
        end_date=date(2026, 6, 15),
        start_time=time(19, 0),
        day_of_month=15,
    )
    created = expand_recurrence(rule)
    assert len(created) == 6


def test_assignment_picker_filters_by_user_role(client, admin_user, umum_with_lineup, role_wl):
    eligible = User.objects.create_user(username="wl-eligible", password="x")
    eligible.user_roles.add(role_wl)
    User.objects.create_user(username="not-eligible", password="x")

    schedule = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=timezone.now() + timedelta(days=1)
    )
    wl_assignment = schedule.assignments.filter(user_role=role_wl).first()

    client.force_login(admin_user)
    response = client.get(reverse("ministry:assignment_picker", args=[wl_assignment.pk]))
    assert response.status_code == 200
    body = response.content.decode()
    assert "wl-eligible" in body
    assert "not-eligible" not in body


def test_viewer_cannot_use_picker(client, db, umum_with_lineup, role_wl):
    viewer = User.objects.create_user(username="v", password="x", account_role=AccountRole.VIEWER)
    schedule = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=timezone.now() + timedelta(days=1)
    )
    a = schedule.assignments.first()
    client.force_login(viewer)
    response = client.get(reverse("ministry:assignment_picker", args=[a.pk]))
    assert response.status_code == 403


def test_assignment_assign_then_clear(client, admin_user, umum_with_lineup, role_wl):
    target = User.objects.create_user(username="target", password="x", full_name="Target Name")
    target.user_roles.add(role_wl)
    schedule = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=timezone.now() + timedelta(days=1)
    )
    a = schedule.assignments.filter(user_role=role_wl).first()

    client.force_login(admin_user)
    response = client.post(
        reverse("ministry:assignment_assign", args=[a.pk]),
        data={"user_id": target.pk},
    )
    assert response.status_code == 200
    a.refresh_from_db()
    assert a.user == target

    response = client.post(reverse("ministry:assignment_clear", args=[a.pk]))
    assert response.status_code == 200
    a.refresh_from_db()
    assert a.user is None


def test_schedule_list_login_required(client, db):
    response = client.get("/")
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


def test_assignment_add_appends_new_slot(client, admin_user, umum_with_lineup, role_wl):
    schedule = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=timezone.now() + timedelta(days=1)
    )
    initial_count = schedule.assignments.filter(user_role=role_wl).count()

    client.force_login(admin_user)
    response = client.post(reverse("ministry:assignment_add", args=[schedule.pk, role_wl.pk]))
    assert response.status_code == 200
    assert schedule.assignments.filter(user_role=role_wl).count() == initial_count + 1

    # Slot indexes should be unique and sequential
    indexes = list(
        schedule.assignments.filter(user_role=role_wl)
        .order_by("slot_index")
        .values_list("slot_index", flat=True)
    )
    assert indexes == list(range(initial_count + 1))


def test_assignment_delete_only_when_empty(client, admin_user, umum_with_lineup, role_singer):
    """Singer has count=3 so we can delete one and still have others to test fill-refusal."""
    target = User.objects.create_user(username="t", password="x")
    target.user_roles.add(role_singer)
    schedule = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=timezone.now() + timedelta(days=1)
    )
    singer_slots = list(schedule.assignments.filter(user_role=role_singer))
    assert len(singer_slots) == 3
    empty_slot, fillable_slot = singer_slots[0], singer_slots[1]

    client.force_login(admin_user)
    response = client.post(reverse("ministry:assignment_delete", args=[empty_slot.pk]))
    assert response.status_code == 200
    assert not Assignment.objects.filter(pk=empty_slot.pk).exists()

    fillable_slot.user = target
    fillable_slot.save()
    response = client.post(reverse("ministry:assignment_delete", args=[fillable_slot.pk]))
    assert response.status_code == 409
    assert Assignment.objects.filter(pk=fillable_slot.pk).exists()


def test_pelayanan_slot_move_up_swaps_with_predecessor(
    client, admin_user, umum_with_lineup, role_wl, role_singer
):
    pelayanan = umum_with_lineup
    # initial order: WL=10, Singer=20
    wl_slot = PelayananRoleSlot.objects.get(pelayanan=pelayanan, user_role=role_wl)
    singer_slot = PelayananRoleSlot.objects.get(pelayanan=pelayanan, user_role=role_singer)
    assert wl_slot.order < singer_slot.order

    client.force_login(admin_user)
    response = client.post(
        reverse("ministry:pelayanan_slots", args=[pelayanan.pk]),
        data={"action": "move_down", "slot_id": wl_slot.pk},
    )
    assert response.status_code == 302

    wl_slot.refresh_from_db()
    singer_slot.refresh_from_db()
    # After move_down, Singer should come before WL
    assert singer_slot.order < wl_slot.order
    # Orders renumbered to clean 10, 20
    assert {singer_slot.order, wl_slot.order} == {10, 20}


def test_pelayanan_slot_move_disallowed_at_edge(client, admin_user, umum_with_lineup, role_wl):
    """Moving the topmost slot up is a no-op (button is disabled in UI but server is also safe)."""
    pelayanan = umum_with_lineup
    wl_slot = PelayananRoleSlot.objects.get(pelayanan=pelayanan, user_role=role_wl)
    original_order = wl_slot.order

    client.force_login(admin_user)
    client.post(
        reverse("ministry:pelayanan_slots", args=[pelayanan.pk]),
        data={"action": "move_up", "slot_id": wl_slot.pk},
    )
    wl_slot.refresh_from_db()
    assert wl_slot.order == original_order


def test_pelayanan_add_slot_appends_to_end(client, admin_user, umum_with_lineup, db):
    """A newly added slot should land at the bottom (max order + 10)."""
    pelayanan = umum_with_lineup
    new_role = UserRole.objects.create(name="Drum", order=999)
    max_before = pelayanan.role_slots.aggregate(m=models.Max("order"))["m"]

    client.force_login(admin_user)
    response = client.post(
        reverse("ministry:pelayanan_slots", args=[pelayanan.pk]),
        data={
            "action": "add",
            "user_role": new_role.pk,
            "count": "2",
        },
    )
    assert response.status_code == 302

    new_slot = pelayanan.role_slots.get(user_role=new_role)
    assert new_slot.order == max_before + 10


def test_viewer_cannot_add_or_delete_slots(client, db, umum_with_lineup, role_wl):
    viewer = User.objects.create_user(username="v2", password="x", account_role=AccountRole.VIEWER)
    schedule = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=timezone.now() + timedelta(days=1)
    )
    a = schedule.assignments.first()
    client.force_login(viewer)
    assert (
        client.post(reverse("ministry:assignment_add", args=[schedule.pk, role_wl.pk])).status_code
        == 403
    )
    assert client.post(reverse("ministry:assignment_delete", args=[a.pk])).status_code == 403


def test_build_schedule_matrix_groups_by_role_and_schedule(
    db, admin_user, umum_with_lineup, role_wl, role_singer
):
    from ministry.views import _build_schedule_matrix

    alice = User.objects.create_user(username="alice", password="x", full_name="Alice")
    bob = User.objects.create_user(username="bob", password="x", full_name="Bob")

    s1 = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=timezone.now() + timedelta(days=1)
    )
    s2 = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=timezone.now() + timedelta(days=8)
    )

    s1.assignments.filter(user_role=role_wl).update(user=alice)
    s1_singer_slots = list(s1.assignments.filter(user_role=role_singer))
    s1_singer_slots[0].user = alice
    s1_singer_slots[0].save()
    s1_singer_slots[1].user = bob
    s1_singer_slots[1].save()
    s2.assignments.filter(user_role=role_wl).update(user=bob)

    schedules = list(
        Schedule.objects.select_related("pelayanan")
        .prefetch_related("assignments__user", "assignments__user_role")
        .filter(pk__in=[s1.pk, s2.pk])
        .order_by("start_at")
    )

    matrix = _build_schedule_matrix(schedules, str(umum_with_lineup.pk))

    assert [d["schedule"].pk for d in matrix["dates"]] == [s1.pk, s2.pk]
    assert [r["role"].pk for r in matrix["rows"]] == [role_wl.pk, role_singer.pk]

    wl_row = matrix["rows"][0]
    singer_row = matrix["rows"][1]
    assert wl_row["cells"] == [["Alice"], ["Bob"]]
    assert singer_row["cells"] == [["Alice", "Bob"], []]


def test_schedule_list_defaults_to_seven_day_window(
    client, admin_user, umum_with_lineup
):
    today = timezone.now()
    s_in = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=today + timedelta(days=3)
    )
    s_out = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=today + timedelta(days=12)
    )

    client.force_login(admin_user)
    response = client.get(reverse("ministry:schedule_list"))
    body = response.content.decode()

    assert response.status_code == 200
    assert reverse("ministry:schedule_detail", args=[s_in.pk]) in body
    assert reverse("ministry:schedule_detail", args=[s_out.pk]) not in body
    # Default window values surface as values on the date inputs
    assert timezone.localdate().isoformat() in body
    assert (timezone.localdate() + timedelta(days=7)).isoformat() in body


def test_schedule_list_explicit_empty_dates_disables_defaults(
    client, admin_user, umum_with_lineup
):
    today = timezone.now()
    s_far = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=today + timedelta(days=12)
    )

    client.force_login(admin_user)
    response = client.get(
        reverse("ministry:schedule_list"),
        {"date_from": "", "date_to": ""},
    )
    body = response.content.decode()

    assert response.status_code == 200
    # With both date keys present (even empty), defaults are skipped — the
    # default upcoming-only filter still includes the +12d schedule.
    assert reverse("ministry:schedule_detail", args=[s_far.pk]) in body


def test_schedule_list_filters_by_date_range(
    client, admin_user, umum_with_lineup
):
    today = timezone.now()
    s_in_window = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=today + timedelta(days=3)
    )
    s_outside_window = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=today + timedelta(days=20)
    )

    client.force_login(admin_user)
    date_from = (today + timedelta(days=1)).date().isoformat()
    date_to = (today + timedelta(days=10)).date().isoformat()
    response = client.get(
        reverse("ministry:schedule_list"),
        {"date_from": date_from, "date_to": date_to},
    )
    body = response.content.decode()

    assert response.status_code == 200
    assert reverse("ministry:schedule_detail", args=[s_in_window.pk]) in body
    assert reverse("ministry:schedule_detail", args=[s_outside_window.pk]) not in body


def test_schedule_list_matrix_view_renders_role_rows(
    client, admin_user, umum_with_lineup, role_wl
):
    user = User.objects.create_user(username="alice2", password="x", full_name="Alice X")
    schedule = create_one_off_schedule(
        pelayanan=umum_with_lineup, start_at=timezone.now() + timedelta(days=2)
    )
    schedule.assignments.filter(user_role=role_wl).update(user=user)

    client.force_login(admin_user)
    response = client.get(
        reverse("ministry:schedule_list"),
        {"view": "matrix", "pelayanan": umum_with_lineup.pk},
    )
    assert response.status_code == 200
    body = response.content.decode()
    assert "Worship Leader" in body
    assert "Alice X" in body
    assert "Task / Date" in body or "Tugas / Tanggal" in body
