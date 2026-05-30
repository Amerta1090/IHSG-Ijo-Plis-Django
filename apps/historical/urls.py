from django.urls import path

from . import views

app_name = "historical"

urlpatterns = [
    path("", views.HistoricalListView.as_view(), name="list"),
    path("upload/", views.UploadCSVView.as_view(), name="upload"),
    path("delete/", views.delete_historical, name="delete"),
    path("delete-all/", views.delete_all_historical, name="delete_all"),
    path("confirm-upload/", views.confirm_upload, name="confirm_upload"),
    path("cancel-upload/", views.cancel_upload, name="cancel_upload"),
]
