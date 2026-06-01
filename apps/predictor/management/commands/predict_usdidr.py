from django.core.management.base import BaseCommand
from django.db import transaction

from apps.predictor.models import UsdIdrPredictionResult
from apps.predictor.services import PredictionService


class Command(BaseCommand):
    help = "Generate USD/IDR predictions using the pre-trained model"

    def add_arguments(self, parser):
        parser.add_argument("--periods", type=int, default=90, help="Days to predict")

    def handle(self, *args, **options):
        periods = options["periods"]

        self.stdout.write("Loading USD/IDR model...")
        try:
            PredictionService.load_model(market="usdidr")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Model load failed: {e}"))
            return

        self.stdout.write(f"Predicting {periods} days for USD/IDR...")
        try:
            result = PredictionService.predict(periods=periods, market="usdidr")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Prediction failed: {e}"))
            return

        inserted = 0
        skipped = 0
        model_version = "usdidr_pretrained"
        with transaction.atomic():
            for row in result:
                _, created = UsdIdrPredictionResult.objects.update_or_create(
                    date=row["ds"].date(),
                    model_version=model_version,
                    defaults={
                        "yhat": round(float(row["yhat"]), 2),
                        "yhat_lower": round(float(row["yhat_lower"]), 2),
                        "yhat_upper": round(float(row["yhat_upper"]), 2),
                    },
                )
                if created:
                    inserted += 1
                else:
                    skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Inserted: {inserted}, Updated: {skipped}, Total: {len(result)}"
            )
        )
