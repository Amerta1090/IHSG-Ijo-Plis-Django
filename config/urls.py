from django.shortcuts import render
from django.urls import path

from apps.predictor.views import about, decomposition_api, index, metrics_api


def handler404(request, exception):
    return render(request, "404.html", status=404)


def handler500(request):
    return render(request, "500.html", status=500)


urlpatterns = [
    path("", index, name="index"),
    path("about/", about, name="about"),
    path("api/metrics.json", metrics_api, name="metrics-api"),
    path("api/decomposition.json", decomposition_api, name="decomposition-api"),
]
