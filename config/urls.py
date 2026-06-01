from django.shortcuts import render
from django.urls import path

from apps.predictor.views import (
    about,
    dashboard,
    decomposition_api,
    metrics_api,
    usdidr_decomposition_api,
    usdidr_metrics_api,
)


def handler404(request, exception):
    return render(request, "404.html", status=404)


def handler500(request):
    return render(request, "500.html", status=500)


urlpatterns = [
    path("", dashboard, {"market": "ihsg"}, name="index"),
    path("usdidr/", dashboard, {"market": "usdidr"}, name="usdidr-dashboard"),
    path("about/", about, name="about"),
    path("api/metrics.json", metrics_api, name="metrics-api"),
    path("api/usdidr/metrics.json", usdidr_metrics_api, name="usdidr-metrics-api"),
    path("api/decomposition.json", decomposition_api, name="decomposition-api"),
    path(
        "api/usdidr/decomposition.json",
        usdidr_decomposition_api,
        name="usdidr-decomposition-api",
    ),
]
