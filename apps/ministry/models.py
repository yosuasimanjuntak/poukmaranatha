from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Pelayanan(models.Model):
    """A worship-service category, e.g. Umum, Sekolah Minggu."""

    name = models.CharField(_("name"), max_length=100, unique=True)
    name_en = models.CharField(_("name (English)"), max_length=100, blank=True)
    description = models.TextField(_("description"), blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    order = models.PositiveIntegerField(_("display order"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = _("pelayanan")
        verbose_name_plural = _("pelayanan")

    def __str__(self):
        return self.name


class UserRole(models.Model):
    """A ministry position someone serves in, e.g. Worship Leader, Drum."""

    name = models.CharField(_("name"), max_length=100, unique=True)
    name_en = models.CharField(_("name (English)"), max_length=100, blank=True)
    description = models.TextField(_("description"), blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    order = models.PositiveIntegerField(_("display order"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = _("ministry role")
        verbose_name_plural = _("ministry roles")

    def __str__(self):
        return self.name


class PelayananRoleSlot(models.Model):
    """Template lineup: how many of a given role a Pelayanan needs."""

    pelayanan = models.ForeignKey(Pelayanan, on_delete=models.CASCADE, related_name="role_slots")
    user_role = models.ForeignKey(UserRole, on_delete=models.PROTECT)
    count = models.PositiveIntegerField(_("count"), default=1)
    order = models.PositiveIntegerField(_("display order"), default=0)

    class Meta:
        ordering = ["order", "user_role__order"]
        unique_together = [("pelayanan", "user_role")]
        verbose_name = _("role slot template")
        verbose_name_plural = _("role slot templates")

    def __str__(self):
        return f"{self.pelayanan.name} · {self.count}× {self.user_role.name}"


class RecurrenceRule(models.Model):
    class Frequency(models.TextChoices):
        DAILY = "daily", _("Daily")
        WEEKLY = "weekly", _("Weekly")
        MONTHLY = "monthly", _("Monthly")

    frequency = models.CharField(_("frequency"), max_length=10, choices=Frequency.choices)
    pelayanan = models.ForeignKey(Pelayanan, on_delete=models.PROTECT, related_name="recurrences")
    start_date = models.DateField(_("start date"))
    end_date = models.DateField(_("end date"))
    start_time = models.TimeField(_("start time"))
    duration_minutes = models.PositiveIntegerField(_("duration (minutes)"), default=90)
    weekday = models.PositiveSmallIntegerField(_("weekday"), null=True, blank=True)
    day_of_month = models.PositiveSmallIntegerField(_("day of month"), null=True, blank=True)
    location = models.CharField(_("location"), max_length=200, blank=True)
    notes = models.TextField(_("notes"), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_recurrences",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("recurrence rule")
        verbose_name_plural = _("recurrence rules")

    def __str__(self):
        return (
            f"{self.get_frequency_display()} · {self.pelayanan.name} · "
            f"{self.start_date}→{self.end_date}"
        )


class Schedule(models.Model):
    """A concrete instance of a Pelayanan at a specific date/time."""

    pelayanan = models.ForeignKey(Pelayanan, on_delete=models.PROTECT, related_name="schedules")
    start_at = models.DateTimeField(_("start at"))
    end_at = models.DateTimeField(_("end at"), null=True, blank=True)
    location = models.CharField(_("location"), max_length=200, blank=True)
    notes = models.TextField(_("notes"), blank=True)
    recurrence = models.ForeignKey(
        RecurrenceRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="schedules",
    )
    is_cancelled = models.BooleanField(_("cancelled"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at"]
        indexes = [
            models.Index(fields=["start_at"]),
            models.Index(fields=["pelayanan", "start_at"]),
        ]
        verbose_name = _("schedule")
        verbose_name_plural = _("schedules")

    def __str__(self):
        return f"{self.pelayanan.name} @ {self.start_at:%Y-%m-%d %H:%M}"


class Assignment(models.Model):
    """One role slot for one schedule, possibly filled by a user."""

    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name="assignments")
    user_role = models.ForeignKey(UserRole, on_delete=models.PROTECT)
    slot_index = models.PositiveIntegerField(_("slot index"), default=0)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments",
    )
    notes = models.CharField(_("notes"), max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user_role__order", "slot_index"]
        unique_together = [("schedule", "user_role", "slot_index")]
        verbose_name = _("assignment")
        verbose_name_plural = _("assignments")

    def __str__(self):
        who = self.user.display_name if self.user else "(empty)"
        return f"{self.schedule} · {self.user_role.name} #{self.slot_index} · {who}"


class Kolekte(models.Model):
    """Offering / collection record tied to one Schedule."""

    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name="kolekte_entries"
    )
    type = models.CharField(_("type"), max_length=100)
    total = models.PositiveIntegerField(_("total (IDR)"))
    notes = models.TextField(_("notes"), blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_kolekte",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["type", "pk"]
        verbose_name = _("kolekte")
        verbose_name_plural = _("kolekte")

    def __str__(self):
        return f"{self.schedule} · {self.type} · Rp {self.total:,}"
