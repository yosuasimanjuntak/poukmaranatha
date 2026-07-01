"""Recurrence expansion + assignment materialization services."""

from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from .models import (
    Assignment,
    Pelayanan,
    PelayananRoleSlot,
    RecurrenceRule,
    Schedule,
)


def _combine(d: date, t: time) -> datetime:
    """Combine a date and time into a timezone-aware datetime in current TZ."""
    return timezone.make_aware(datetime.combine(d, t))


def _occurrences(rule: RecurrenceRule) -> list[date]:
    """Yield all dates in [start_date, end_date] matching the rule."""
    out: list[date] = []
    d = rule.start_date
    end = rule.end_date

    if rule.frequency == RecurrenceRule.Frequency.DAILY:
        while d <= end:
            out.append(d)
            d += timedelta(days=1)

    elif rule.frequency == RecurrenceRule.Frequency.WEEKLY:
        target_weekday = rule.weekday if rule.weekday is not None else d.weekday()
        # Advance d to first occurrence of target weekday >= start_date
        delta = (target_weekday - d.weekday()) % 7
        d = d + timedelta(days=delta)
        while d <= end:
            out.append(d)
            d += timedelta(days=7)

    elif rule.frequency == RecurrenceRule.Frequency.MONTHLY:
        dom = rule.day_of_month if rule.day_of_month is not None else d.day
        year, month = d.year, d.month
        while True:
            try:
                candidate = date(year, month, dom)
            except ValueError:
                # Day doesn't exist this month (e.g. Feb 30); skip month
                candidate = None
            if candidate is not None and rule.start_date <= candidate <= end:
                out.append(candidate)
            if candidate is None or candidate <= end:
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                if date(year, month, 1) > end:
                    break
            else:
                break

    return out


def materialize_assignments(schedule: Schedule) -> list[Assignment]:
    """Create empty Assignment rows for every role slot of the schedule's Pelayanan.

    Idempotent: if assignments already exist for this schedule, do nothing.
    """
    if schedule.assignments.exists():
        return []

    slots = PelayananRoleSlot.objects.filter(pelayanan=schedule.pelayanan).select_related(
        "user_role"
    )
    new_assignments: list[Assignment] = []
    for slot in slots:
        for i in range(slot.count):
            new_assignments.append(
                Assignment(
                    schedule=schedule,
                    user_role=slot.user_role,
                    slot_index=i,
                )
            )
    return Assignment.objects.bulk_create(new_assignments)


@transaction.atomic
def expand_recurrence(rule: RecurrenceRule) -> list[Schedule]:
    """Create one Schedule + assignments per occurrence covered by `rule`."""
    created: list[Schedule] = []
    duration = timedelta(minutes=rule.duration_minutes)
    for d in _occurrences(rule):
        start_at = _combine(d, rule.start_time)
        sched = Schedule.objects.create(
            pelayanan=rule.pelayanan,
            start_at=start_at,
            end_at=start_at + duration,
            location=rule.location,
            notes=rule.notes,
            recurrence=rule,
        )
        materialize_assignments(sched)
        created.append(sched)
    return created


@transaction.atomic
def create_one_off_schedule(
    *,
    pelayanan: Pelayanan,
    start_at: datetime,
    duration_minutes: int = 90,
    location: str = "",
    notes: str = "",
    end_at: datetime | None = None,
) -> Schedule:
    if end_at is None:
        end_at = start_at + timedelta(minutes=duration_minutes)
    schedule = Schedule.objects.create(
        pelayanan=pelayanan,
        start_at=start_at,
        end_at=end_at,
        location=location,
        notes=notes,
    )
    materialize_assignments(schedule)
    return schedule
