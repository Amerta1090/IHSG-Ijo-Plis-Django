from django.core.management.base import BaseCommand
from django.db import transaction

from apps.predictor.models import ModelVersion, PredictionResult
from apps.predictor.services import PredictionService


class Command(BaseCommand):
    help = "Generate predictions using the active model"

    def add_arguments(self, parser):
        parser.add_argument("--periods", type=int, default=90, help="Days to predict")

    def handle(self, *args, **options):
        periods = options["periods"]

        try:
            active = ModelVersion.objects.filter(is_active=True).first()
        except Exception:
            active = None

        model_version = active.version if active else "unknown"
        self.stdout.write(f"Predicting {periods} days using model v{model_version}...")

        try:
            result = PredictionService.predict(periods=periods)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Prediction failed: {e}"))
            return

        inserted = 0
        skipped = 0
        with transaction.atomic():
            for row in result:
                _, created = PredictionResult.objects.update_or_create(
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
