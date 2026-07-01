from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Kolekte, Pelayanan, PelayananRoleSlot, RecurrenceRule, Schedule, UserRole


class PelayananForm(forms.ModelForm):
    class Meta:
        model = Pelayanan
        fields = ["name", "name_en", "description", "is_active", "order"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class UserRoleForm(forms.ModelForm):
    class Meta:
        model = UserRole
        fields = ["name", "name_en", "description", "is_active", "order"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class PelayananRoleSlotForm(forms.ModelForm):
    class Meta:
        model = PelayananRoleSlot
        fields = ["user_role", "count"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user_role"].queryset = UserRole.objects.filter(is_active=True)


class ScheduleForm(forms.ModelForm):
    duration_minutes = forms.IntegerField(
        label=_("Duration (minutes)"),
        min_value=1,
        initial=90,
        required=False,
    )

    class Meta:
        model = Schedule
        fields = ["pelayanan", "start_at", "location", "notes"]
        widgets = {
            "start_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pelayanan"].queryset = Pelayanan.objects.filter(is_active=True)
        self.fields["start_at"].input_formats = ["%Y-%m-%dT%H:%M"]


class RecurrenceForm(forms.ModelForm):
    class Meta:
        model = RecurrenceRule
        fields = [
            "pelayanan",
            "frequency",
            "start_date",
            "end_date",
            "start_time",
            "duration_minutes",
            "weekday",
            "day_of_month",
            "location",
            "notes",
        ]
        widgets = {
            "frequency": forms.Select(attrs={"x-model": "frequency"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "weekday": forms.Select(
                choices=[
                    ("", _("(auto from start date)")),
                    (0, _("Monday")),
                    (1, _("Tuesday")),
                    (2, _("Wednesday")),
                    (3, _("Thursday")),
                    (4, _("Friday")),
                    (5, _("Saturday")),
                    (6, _("Sunday")),
                ]
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pelayanan"].queryset = Pelayanan.objects.filter(is_active=True)

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            raise forms.ValidationError(_("End date must be on or after start date."))
        return cleaned


KOLEKTE_TYPE_CHOICES = [
    ("Kolekte", _("Kolekte")),
    ("Kotak Pembangunan", _("Kotak Pembangunan")),
    ("Persepuluhan", _("Persepuluhan")),
    ("Lainnya", _("Lainnya")),
]


class KolekteForm(forms.ModelForm):
    type = forms.ChoiceField(
        label=_("Type"),
        choices=KOLEKTE_TYPE_CHOICES,
    )

    class Meta:
        model = Kolekte
        fields = ["type", "total", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
