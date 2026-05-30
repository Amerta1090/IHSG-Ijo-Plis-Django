from django.core.management.base import BaseCommand

from apps.prediction.services import PredictionService


class Command(BaseCommand):
    help = "Load the Prophet model and verify it works"

    def handle(self, *args, **options):
        self.stdout.write("Loading Prophet model...")
        try:
            model = PredictionService.load_model()
            model_name = type(model).__name__
            self.stdout.write(self.style.SUCCESS(f"Model loaded: {model_name}"))
            self.stdout.write("Running test prediction...")
            result = PredictionService.predict(periods=5)
            self.stdout.write(self.style.SUCCESS(f"Prediction OK: {len(result)} rows"))
            for row in result:
                self.stdout.write(
                    f"  {row['ds'].strftime('%Y-%m-%d')}: "
                    f"yhat={row['yhat']:.2f} "
                    f"[{row['yhat_lower']:.2f} - {row['yhat_upper']:.2f}]"
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            raise
