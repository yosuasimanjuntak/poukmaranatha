from datetime import datetime, timedelta
from itertools import groupby

from accounts.permissions import is_admin_or_above
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from .forms import (
    KolekteForm,
    PelayananForm,
    PelayananRoleSlotForm,
    RecurrenceForm,
    ScheduleForm,
    UserRoleForm,
)
from .models import Assignment, Kolekte, Pelayanan, PelayananRoleSlot, Schedule, UserRole
from .services import create_one_off_schedule, expand_recurrence, materialize_assignments


def _parse_iso_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _filter_schedules(request: HttpRequest):
    qs = (
        Schedule.objects.select_related("pelayanan")
        .prefetch_related("assignments__user", "assignments__user_role")
        .filter(is_cancelled=False)
    )

    # Defaults apply only on a fresh URL (no date params at all). Once the form
    # has submitted, both keys are present (possibly empty) and the user's
    # explicit choice — including an explicit clear — wins.
    raw_from = request.GET.get("date_from")
    raw_to = request.GET.get("date_to")
    if raw_from is None and raw_to is None:
        today = timezone.localdate()
        date_from = today
        date_to = today + timedelta(days=7)
        date_from_raw = date_from.isoformat()
        date_to_raw = date_to.isoformat()
    else:
        date_from_raw = raw_from or ""
        date_to_raw = raw_to or ""
        date_from = _parse_iso_date(date_from_raw)
        date_to = _parse_iso_date(date_to_raw)

    if date_from:
        qs = qs.filter(start_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(start_at__date__lte=date_to)

    show_past = request.GET.get("past") == "1"
    # If the user picks a date range, that fully scopes the query. Without one,
    # default to upcoming-only (unless the past toggle is on).
    if not show_past and not date_from and not date_to:
        qs = qs.filter(start_at__gte=timezone.now())

    pelayanan_id = request.GET.get("pelayanan") or ""
    if pelayanan_id:
        qs = qs.filter(pelayanan_id=pelayanan_id)

    user_role_id = request.GET.get("user_role") or ""
    if user_role_id:
        qs = qs.filter(assignments__user_role_id=user_role_id).distinct()

    return qs.order_by("start_at"), {
        "selected_pelayanan": pelayanan_id,
        "selected_user_role": user_role_id,
        "show_past": show_past,
        "date_from": date_from_raw if date_from else "",
        "date_to": date_to_raw if date_to else "",
    }


def _build_schedule_matrix(schedules, pelayanan_id: str) -> dict:
    """Build a (roles × schedules) pivot from a prefetched list of Schedules."""
    if pelayanan_id:
        slots = (
            PelayananRoleSlot.objects.filter(
                pelayanan_id=pelayanan_id, user_role__is_active=True
            )
            .select_related("user_role")
            .order_by("order", "user_role__order")
        )
        roles = [slot.user_role for slot in slots]
    else:
        role_ids: set[int] = set()
        for s in schedules:
            for a in s.assignments.all():
                if a.user_id:
                    role_ids.add(a.user_role_id)
        roles = list(
            UserRole.objects.filter(pk__in=role_ids, is_active=True).order_by(
                "order", "name"
            )
        )

    cells: dict[tuple[int, int], list[str]] = {}
    for s in schedules:
        for a in s.assignments.all():
            if a.user_id is None:
                continue
            cells.setdefault((a.user_role_id, s.id), []).append(a.user.display_name)
    for names in cells.values():
        names.sort(key=str.casefold)

    from django.template.defaultfilters import date as date_filter

    dates = []
    for s in schedules:
        local_dt = timezone.localtime(s.start_at)
        dates.append(
            {
                "schedule": s,
                "weekday_label": date_filter(local_dt, "D"),
                "day_label": date_filter(local_dt, "j"),
                "month_label": date_filter(local_dt, "M"),
            }
        )
    rows = [
        {
            "role": role,
            "cells": [cells.get((role.id, s.id), []) for s in schedules],
        }
        for role in roles
    ]
    return {"dates": dates, "rows": rows}


@login_required
def schedule_list(request: HttpRequest) -> HttpResponse:
    qs, filters = _filter_schedules(request)
    schedules = list(qs[:200])
    view_mode = "matrix" if request.GET.get("view") == "matrix" else "list"

    context = {
        "view": view_mode,
        "pelayanan_options": Pelayanan.objects.filter(is_active=True),
        "user_role_options": UserRole.objects.filter(is_active=True),
        **filters,
    }

    if view_mode == "matrix":
        selected_pelayanan_obj = None
        if filters["selected_pelayanan"]:
            selected_pelayanan_obj = Pelayanan.objects.filter(
                pk=filters["selected_pelayanan"]
            ).first()
        context["matrix"] = _build_schedule_matrix(
            schedules, filters["selected_pelayanan"]
        )
        context["selected_pelayanan_obj"] = selected_pelayanan_obj
        partial = "ministry/_schedule_matrix.html"
    else:
        schedules_by_date = [
            (day, list(group))
            for day, group in groupby(
                schedules, key=lambda s: timezone.localtime(s.start_at).date()
            )
        ]
        context["schedules_by_date"] = schedules_by_date
        partial = "ministry/_schedule_results.html"

    if request.htmx:
        return render(request, partial, context)
    return render(request, "ministry/schedule_list.html", context)


@login_required
def my_schedule(request: HttpRequest) -> HttpResponse:
    show_past = request.GET.get("past") == "1"
    qs = (
        Assignment.objects.filter(user=request.user, schedule__is_cancelled=False)
        .select_related("schedule", "schedule__pelayanan", "user_role")
        .order_by("schedule__start_at")
    )
    if not show_past:
        qs = qs.filter(schedule__start_at__gte=timezone.now())

    assignments = list(qs[:200])
    assignments_by_date = [
        (
            day,
            list(group),
        )
        for day, group in groupby(
            assignments,
            key=lambda a: timezone.localtime(a.schedule.start_at).date(),
        )
    ]
    return render(
        request,
        "ministry/my_schedule.html",
        {"assignments_by_date": assignments_by_date, "show_past": show_past},
    )


@login_required
def schedule_detail(request: HttpRequest, pk: int) -> HttpResponse:
    schedule = get_object_or_404(
        Schedule.objects.select_related("pelayanan").prefetch_related(
            "assignments__user", "assignments__user_role"
        ),
        pk=pk,
    )

    grouped: dict[UserRole, list[Assignment]] = {}
    for assignment in schedule.assignments.all():
        grouped.setdefault(assignment.user_role, []).append(assignment)

    role_groups = sorted(
        grouped.items(),
        key=lambda item: (item[0].order, item[0].name),
    )
    for _role, items in role_groups:
        items.sort(key=lambda a: a.slot_index)

    kolekte_entries = list(schedule.kolekte_entries.all())
    grand_total = sum(e.total for e in kolekte_entries)

    return render(
        request,
        "ministry/schedule_detail.html",
        {
            "schedule": schedule,
            "role_groups": role_groups,
            "entries": kolekte_entries,
            "grand_total": grand_total,
            "form": KolekteForm() if is_admin_or_above(request.user) else None,
        },
    )


@login_required
def schedule_create(request: HttpRequest) -> HttpResponse:
    if not is_admin_or_above(request.user):
        return HttpResponse(status=403)

    mode = request.GET.get("mode") or request.POST.get("mode") or "one_off"

    if request.method == "POST":
        if mode == "recurring":
            form = RecurrenceForm(request.POST)
            if form.is_valid():
                rule = form.save(commit=False)
                rule.created_by = request.user
                rule.save()
                created = expand_recurrence(rule)
                messages.success(
                    request,
                    _("Created %(count)d schedule instances.") % {"count": len(created)},
                )
                return redirect("ministry:schedule_list")
        else:
            form = ScheduleForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                schedule = create_one_off_schedule(
                    pelayanan=cd["pelayanan"],
                    start_at=cd["start_at"],
                    duration_minutes=cd.get("duration_minutes") or 90,
                    location=cd.get("location") or "",
                    notes=cd.get("notes") or "",
                )
                messages.success(request, _("Schedule created."))
                return redirect("ministry:schedule_detail", pk=schedule.pk)
    else:
        form = RecurrenceForm() if mode == "recurring" else ScheduleForm()

    return render(
        request,
        "ministry/schedule_form.html",
        {"form": form, "mode": mode},
    )


@login_required
def schedule_edit(request: HttpRequest, pk: int) -> HttpResponse:
    if not is_admin_or_above(request.user):
        return HttpResponse(status=403)
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == "POST":
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            # Re-materialize if pelayanan changed and no assignments yet
            materialize_assignments(schedule)
            messages.success(request, _("Schedule updated."))
            return redirect("ministry:schedule_detail", pk=schedule.pk)
    else:
        form = ScheduleForm(instance=schedule)
    return render(
        request,
        "ministry/schedule_form.html",
        {"form": form, "mode": "edit", "schedule": schedule},
    )


# ---------- Assignment HTMX flows ----------

from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()


def _admin_only_htmx(request: HttpRequest):
    if not request.user.is_authenticated:
        return HttpResponse(status=401)
    if not is_admin_or_above(request.user):
        return HttpResponse(status=403)
    return None


@login_required
def assignment_picker(request: HttpRequest, assignment_pk: int) -> HttpResponse:
    """Render a user picker filtered to people who have this slot's UserRole."""
    if (denied := _admin_only_htmx(request)) is not None:
        return denied
    assignment = get_object_or_404(
        Assignment.objects.select_related("user_role", "schedule"), pk=assignment_pk
    )
    q = (request.GET.get("q") or "").strip()
    schedule_pelayanan = assignment.schedule.pelayanan
    candidates = (
        User.objects.filter(
            is_active=True,
            user_roles=assignment.user_role,
            pelayanan_categories=schedule_pelayanan,
        )
        .distinct()
        .order_by("full_name", "username")
    )
    if q:
        candidates = candidates.filter(username__icontains=q) | candidates.filter(
            full_name__icontains=q
        )
    return render(
        request,
        "ministry/_user_picker.html",
        {
            "assignment": assignment,
            "candidates": candidates[:50],
            "q": q,
        },
    )


@login_required
def assignment_assign(request: HttpRequest, assignment_pk: int) -> HttpResponse:
    if (denied := _admin_only_htmx(request)) is not None:
        return denied
    if request.method != "POST":
        return HttpResponse(status=405)
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    user_id = request.POST.get("user_id") or None
    if user_id:
        assignment.user = User.objects.get(pk=user_id)
    else:
        assignment.user = None
    assignment.save()
    return render(
        request,
        "ministry/_assignment_row.html",
        {"a": assignment, "is_admin_or_above": True},
    )


@login_required
def assignment_clear(request: HttpRequest, assignment_pk: int) -> HttpResponse:
    if (denied := _admin_only_htmx(request)) is not None:
        return denied
    if request.method != "POST":
        return HttpResponse(status=405)
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    assignment.user = None
    assignment.save()
    return render(
        request,
        "ministry/_assignment_row.html",
        {"a": assignment, "is_admin_or_above": True},
    )


@login_required
def assignment_add(request: HttpRequest, schedule_pk: int, user_role_pk: int) -> HttpResponse:
    """Append a new empty slot for a (schedule, user_role)."""
    if (denied := _admin_only_htmx(request)) is not None:
        return denied
    if request.method != "POST":
        return HttpResponse(status=405)
    schedule = get_object_or_404(Schedule, pk=schedule_pk)
    user_role = get_object_or_404(UserRole, pk=user_role_pk)
    next_index = (
        Assignment.objects.filter(schedule=schedule, user_role=user_role)
        .order_by("-slot_index")
        .values_list("slot_index", flat=True)
        .first()
    )
    next_index = 0 if next_index is None else next_index + 1
    assignment = Assignment.objects.create(
        schedule=schedule, user_role=user_role, slot_index=next_index
    )
    return render(
        request,
        "ministry/_assignment_row.html",
        {"a": assignment, "is_admin_or_above": True, "swap_in_place": True},
    )


@login_required
def assignment_delete(request: HttpRequest, assignment_pk: int) -> HttpResponse:
    """Remove an empty slot entirely. Filled slots must be cleared first."""
    if (denied := _admin_only_htmx(request)) is not None:
        return denied
    if request.method != "POST":
        return HttpResponse(status=405)
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    if assignment.user is not None:
        return HttpResponse(
            status=409,
            content=b"Clear the slot before removing it.",
        )
    assignment.delete()
    return HttpResponse(status=200)


# ---------- Pelayanan CRUD ----------


def _admin_only(request: HttpRequest):
    if not is_admin_or_above(request.user):
        return HttpResponse(status=403)
    return None


@login_required
def pelayanan_list(request: HttpRequest) -> HttpResponse:
    if (d := _admin_only(request)) is not None:
        return d
    return render(
        request,
        "ministry/pelayanan_list.html",
        {"pelayanan_list": Pelayanan.objects.all()},
    )


@login_required
def pelayanan_form(request: HttpRequest, pk: int | None = None) -> HttpResponse:
    if (d := _admin_only(request)) is not None:
        return d
    instance = get_object_or_404(Pelayanan, pk=pk) if pk else None
    if request.method == "POST":
        form = PelayananForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            messages.success(request, _("Pelayanan saved."))
            return redirect("ministry:pelayanan_slots", pk=obj.pk)
    else:
        form = PelayananForm(instance=instance)
    return render(
        request,
        "ministry/pelayanan_form.html",
        {"form": form, "instance": instance},
    )


@login_required
def pelayanan_slots(request: HttpRequest, pk: int) -> HttpResponse:
    """Manage the role-slot lineup for one Pelayanan."""
    if (d := _admin_only(request)) is not None:
        return d
    pelayanan = get_object_or_404(Pelayanan, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action") or ""
        if action == "add":
            form = PelayananRoleSlotForm(request.POST)
            if form.is_valid():
                slot = form.save(commit=False)
                slot.pelayanan = pelayanan
                max_order = pelayanan.role_slots.aggregate(m=models.Max("order"))["m"] or 0
                slot.order = max_order + 10
                slot.save()
                messages.success(request, _("Role slot added."))
            else:
                messages.error(request, _("Could not add role slot."))
        elif action == "delete":
            slot_id = request.POST.get("slot_id")
            if slot_id:
                PelayananRoleSlot.objects.filter(pk=slot_id, pelayanan=pelayanan).delete()
                messages.success(request, _("Role slot removed."))
        elif action == "update":
            slot_id = request.POST.get("slot_id")
            slot = get_object_or_404(PelayananRoleSlot, pk=slot_id, pelayanan=pelayanan)
            form = PelayananRoleSlotForm(request.POST, instance=slot)
            if form.is_valid():
                form.save()
                messages.success(request, _("Slot updated."))
        elif action in ("move_up", "move_down"):
            slot_id = request.POST.get("slot_id")
            slot = get_object_or_404(PelayananRoleSlot, pk=slot_id, pelayanan=pelayanan)
            siblings = list(pelayanan.role_slots.order_by("order", "user_role__order", "pk"))
            idx = next(i for i, s in enumerate(siblings) if s.pk == slot.pk)
            new_idx = idx - 1 if action == "move_up" else idx + 1
            if 0 <= new_idx < len(siblings):
                siblings.insert(new_idx, siblings.pop(idx))
                for i, s in enumerate(siblings):
                    new_order = (i + 1) * 10
                    if s.order != new_order:
                        s.order = new_order
                        s.save(update_fields=["order"])
        return redirect("ministry:pelayanan_slots", pk=pelayanan.pk)

    add_form = PelayananRoleSlotForm()
    slots = pelayanan.role_slots.select_related("user_role").order_by("order", "user_role__order")
    return render(
        request,
        "ministry/pelayanan_slots.html",
        {"pelayanan": pelayanan, "slots": slots, "add_form": add_form},
    )


# ---------- UserRole CRUD ----------


@login_required
def userrole_list(request: HttpRequest) -> HttpResponse:
    if (d := _admin_only(request)) is not None:
        return d
    return render(
        request,
        "ministry/userrole_list.html",
        {"roles": UserRole.objects.all()},
    )


@login_required
def userrole_form(request: HttpRequest, pk: int | None = None) -> HttpResponse:
    if (d := _admin_only(request)) is not None:
        return d
    instance = get_object_or_404(UserRole, pk=pk) if pk else None
    if request.method == "POST":
        form = UserRoleForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _("Ministry role saved."))
            return redirect("ministry:userrole_list")
    else:
        form = UserRoleForm(instance=instance)
    return render(
        request,
        "ministry/userrole_form.html",
        {"form": form, "instance": instance},
    )


# ---------- Kolekte CRUD ----------


@login_required
def kolekte_list(request: HttpRequest, schedule_pk: int) -> HttpResponse:
    schedule = get_object_or_404(Schedule.objects.select_related("pelayanan"), pk=schedule_pk)
    entries = schedule.kolekte_entries.all()
    grand_total = sum(e.total for e in entries)
    form = KolekteForm() if is_admin_or_above(request.user) else None
    context = {
        "schedule": schedule,
        "entries": entries,
        "grand_total": grand_total,
        "form": form,
    }
    if request.htmx:
        return render(request, "ministry/_kolekte_section.html", context)
    return render(request, "ministry/kolekte_list.html", context)


@login_required
def kolekte_add(request: HttpRequest, schedule_pk: int) -> HttpResponse:
    if (denied := _admin_only_htmx(request)) is not None:
        return denied
    if request.method != "POST":
        return HttpResponse(status=405)
    schedule = get_object_or_404(Schedule, pk=schedule_pk)
    form = KolekteForm(request.POST)
    if form.is_valid():
        entry = form.save(commit=False)
        entry.schedule = schedule
        entry.recorded_by = request.user
        entry.save()
    entries = schedule.kolekte_entries.all()
    grand_total = sum(e.total for e in entries)
    return render(
        request,
        "ministry/_kolekte_section.html",
        {"schedule": schedule, "entries": entries, "grand_total": grand_total, "form": KolekteForm()},
    )


@login_required
def kolekte_edit(request: HttpRequest, pk: int) -> HttpResponse:
    if (denied := _admin_only_htmx(request)) is not None:
        return denied
    entry = get_object_or_404(Kolekte.objects.select_related("schedule__pelayanan"), pk=pk)
    if request.method == "POST":
        form = KolekteForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            entries = entry.schedule.kolekte_entries.all()
            grand_total = sum(e.total for e in entries)
            return render(
                request,
                "ministry/_kolekte_section.html",
                {
                    "schedule": entry.schedule,
                    "entries": entries,
                    "grand_total": grand_total,
                    "form": KolekteForm(),
                },
            )
    else:
        form = KolekteForm(instance=entry)
    return render(request, "ministry/_kolekte_edit_form.html", {"entry": entry, "form": form})


@login_required
def kolekte_delete(request: HttpRequest, pk: int) -> HttpResponse:
    if (denied := _admin_only_htmx(request)) is not None:
        return denied
    if request.method != "POST":
        return HttpResponse(status=405)
    entry = get_object_or_404(Kolekte.objects.select_related("schedule__pelayanan"), pk=pk)
    schedule = entry.schedule
    entry.delete()
    entries = schedule.kolekte_entries.all()
    grand_total = sum(e.total for e in entries)
    return render(
        request,
        "ministry/_kolekte_section.html",
        {"schedule": schedule, "entries": entries, "grand_total": grand_total, "form": KolekteForm()},
    )
