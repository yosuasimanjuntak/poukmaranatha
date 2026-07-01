from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("manage/", views.manage_index, name="manage_index"),
    path("manage/users/", views.user_list, name="user_list"),
    path("manage/users/new/", views.user_create, name="user_create"),
    path("manage/users/<int:pk>/", views.user_edit, name="user_edit"),
    path("manage/users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    path("profile/", views.profile_edit, name="profile_edit"),
    path("profile/password/", views.profile_password, name="profile_password"),
]
