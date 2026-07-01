from django.contrib import admin

from .models import (
    Assignment,
    Pelayanan,
    PelayananRoleSlot,
    RecurrenceRule,
    Schedule,
    UserRole,
)


class PelayananRoleSlotInline(admin.TabularInline):
    model = PelayananRoleSlot
    extra = 0
    autocomplete_fields = ("user_role",)


@admin.register(Pelayanan)
class PelayananAdmin(admin.ModelAdmin):
    list_display = ("name", "name_en", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("name", "name_en")
    inlines = [PelayananRoleSlotInline]


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("name", "name_en", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("name", "name_en")


@admin.register(RecurrenceRule)
class RecurrenceRuleAdmin(admin.ModelAdmin):
    list_display = (
        "pelayanan",
        "frequency",
        "start_date",
        "end_date",
        "start_time",
        "weekday",
        "day_of_month",
    )
    list_filter = ("frequency", "pelayanan")
    search_fields = ("pelayanan__name", "notes")
    autocomplete_fields = ("pelayanan",)


class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 0
    autocomplete_fields = ("user_role", "user")


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("pelayanan", "start_at", "location", "is_cancelled", "recurrence")
    list_filter = ("pelayanan", "is_cancelled")
    date_hierarchy = "start_at"
    search_fields = ("pelayanan__name", "location", "notes")
    autocomplete_fields = ("pelayanan", "recurrence")
    inlines = [AssignmentInline]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("schedule", "user_role", "slot_index", "user")
    list_filter = ("user_role",)
    autocomplete_fields = ("schedule", "user_role", "user")
