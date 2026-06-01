from datetime import datetime

from django.core.management.base import BaseCommand

from apps.predictor.models import UsdIdrHistoricalData
from apps.predictor.services import TrainingService


class Command(BaseCommand):
    help = "Train Prophet model on USD/IDR historical data"

    def handle(self, *args, **options):
        qs = UsdIdrHistoricalData.objects.all().order_by("date")
        if not qs.exists():
            msg = "No USD/IDR historical data found. Run fetch_usdidr first."
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
            f"Training USD/IDR on {len(df)} rows ({df['ds'].min()} to {data_end})..."
        )

        try:
            model = TrainingService.train_prophet(df)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Training failed: {e}"))
            return

        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = TrainingService.save_model(model, version, market="usdidr")
        self.stdout.write(self.style.SUCCESS(f"USD/IDR model saved to {path}"))

        metrics = TrainingService.evaluate(model, df)
        self.stdout.write(f"Metrics: MAE={metrics['mae']}, RMSE={metrics['rmse']}")
