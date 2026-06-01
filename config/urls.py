from django.urls import path

from apps.predictor.views import decomposition_api, index, metrics_api

urlpatterns = [
    path("", index, name="index"),
    path("api/metrics.json", metrics_api, name="metrics-api"),
    path("api/decomposition.json", decomposition_api, name="decomposition-api"),
]
