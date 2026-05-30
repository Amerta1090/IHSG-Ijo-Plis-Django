from django.db import models


class HistoricalData(models.Model):
    SOURCE_CHOICES = [
        ("manual", "Manual"),
        ("csv", "CSV Upload"),
    ]

    date = models.DateField(unique=True)
    close = models.FloatField(verbose_name="Closing Price")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="manual")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = "Historical Data"
        verbose_name_plural = "Historical Data"

    def __str__(self) -> str:
        return f"{self.date}: {self.close}"


class UploadedCSV(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("done", "Done"),
        ("error", "Error"),
    ]

    file = models.FileField(upload_to="csv_uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Uploaded CSV"
        verbose_name_plural = "Uploaded CSV"

    def __str__(self) -> str:
        return f"{self.file.name} ({self.status})"
