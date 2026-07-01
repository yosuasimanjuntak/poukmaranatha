from django.urls import path

from . import views

app_name = "ministry"

urlpatterns = [
    path("", views.schedule_list, name="schedule_list"),
    path("me/", views.my_schedule, name="my_schedule"),
    path("schedules/new/", views.schedule_create, name="schedule_create"),
    path("schedules/<int:pk>/", views.schedule_detail, name="schedule_detail"),
    path("schedules/<int:pk>/edit/", views.schedule_edit, name="schedule_edit"),
    path(
        "assignments/<int:assignment_pk>/picker/",
        views.assignment_picker,
        name="assignment_picker",
    ),
    path(
        "assignments/<int:assignment_pk>/assign/",
        views.assignment_assign,
        name="assignment_assign",
    ),
    path(
        "assignments/<int:assignment_pk>/clear/",
        views.assignment_clear,
        name="assignment_clear",
    ),
    path(
        "assignments/<int:assignment_pk>/delete/",
        views.assignment_delete,
        name="assignment_delete",
    ),
    path(
        "schedules/<int:schedule_pk>/roles/<int:user_role_pk>/add/",
        views.assignment_add,
        name="assignment_add",
    ),
    path("manage/pelayanan/", views.pelayanan_list, name="pelayanan_list"),
    path("manage/pelayanan/new/", views.pelayanan_form, name="pelayanan_create"),
    path("manage/pelayanan/<int:pk>/", views.pelayanan_form, name="pelayanan_edit"),
    path(
        "manage/pelayanan/<int:pk>/slots/",
        views.pelayanan_slots,
        name="pelayanan_slots",
    ),
    path("manage/user-roles/", views.userrole_list, name="userrole_list"),
    path("manage/user-roles/new/", views.userrole_form, name="userrole_create"),
    path("manage/user-roles/<int:pk>/", views.userrole_form, name="userrole_edit"),
    path("schedules/<int:schedule_pk>/kolekte/", views.kolekte_list, name="kolekte_list"),
    path("schedules/<int:schedule_pk>/kolekte/add/", views.kolekte_add, name="kolekte_add"),
    path("kolekte/<int:pk>/edit/", views.kolekte_edit, name="kolekte_edit"),
    path("kolekte/<int:pk>/delete/", views.kolekte_delete, name="kolekte_delete"),
]
