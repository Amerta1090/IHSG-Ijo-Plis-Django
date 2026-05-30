from django.contrib import admin

from .models import HistoricalData, UploadedCSV


@admin.register(HistoricalData)
class HistoricalDataAdmin(admin.ModelAdmin):
    list_display = ("date", "close", "source", "created_at")
    list_filter = ("source",)
    search_fields = ("date",)
    date_hierarchy = "date"


@admin.register(UploadedCSV)
class UploadedCSVAdmin(admin.ModelAdmin):
    list_display = ("file", "status", "uploaded_at")
    list_filter = ("status",)
