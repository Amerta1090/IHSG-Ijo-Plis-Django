from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.predictor.models import HistoricalData, ModelVersion
from apps.predictor.services import TrainingService


class Command(BaseCommand):
    help = "Train Prophet model on historical data and save versioned .joblib"

    def handle(self, *args, **options):
        qs = HistoricalData.objects.all().order_by("date")
        if not qs.exists():
            msg = "No historical data found. Run fetch_ihsg first."
            self.stdout.write(self.style.ERROR(msg))
            return

        df = qs.values("date", "close")
        import pandas as pd

        df = (
            pd.DataFrame(df)
            .rename(columns={"date": "ds", "close": "y"})
            .assign(ds=lambda x: pd.to_datetime(x["ds"]))
        )

        data_end = df["ds"].max()
        self.stdout.write(
            f"Training on {len(df)} rows ({df['ds'].min()} to {data_end})..."
        )

        try:
            model = TrainingService.train_prophet(df)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Training failed: {e}"))
            return

        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = TrainingService.save_model(model, version)
        self.stdout.write(self.style.SUCCESS(f"Model saved to {path}"))

        metrics = TrainingService.evaluate(model, df)
        self.stdout.write(f"Metrics: MAE={metrics['mae']}, RMSE={metrics['rmse']}")

        ModelVersion.objects.update(is_active=False)
        ModelVersion.objects.create(
            version=version,
            trained_at=timezone.now(),
            data_end_date=data_end,
            metrics=metrics,
            is_active=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Model v{version} set as active."))
