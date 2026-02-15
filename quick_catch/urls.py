from django.urls import path

from . import views

app_name = "quick_catch"

urlpatterns = [
    path("", views.dump_view, name="dump"),
    path("result/<uuid:dump_id>/", views.result_view, name="result"),
    path("history/", views.dump_list_view, name="dump_list"),
    path("profile/", views.profile_view, name="profile"),
]
