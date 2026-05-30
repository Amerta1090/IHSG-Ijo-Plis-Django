from django.db import models


class HistoricalData(models.Model):
    date = models.DateField(unique=True)
    close = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Historical data"

    def __str__(self) -> str:
        return f"{self.date}: {self.close}"


class PredictionResult(models.Model):
    date = models.DateField()
    yhat = models.FloatField()
    yhat_lower = models.FloatField()
    yhat_upper = models.FloatField()
    model_version = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]
        unique_together = ("date", "model_version")

    def __str__(self) -> str:
        return f"{self.date}: {self.yhat:.2f} (v{self.model_version})"


class ModelVersion(models.Model):
    version = models.CharField(max_length=50, unique=True)
    trained_at = models.DateTimeField()
    data_end_date = models.DateField()
    metrics = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-trained_at"]

    def __str__(self) -> str:
        return f"v{self.version} ({self.trained_at.date()})"
