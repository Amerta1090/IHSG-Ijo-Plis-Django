from django.core.management.base import BaseCommand

from apps.predictor.models import UsdIdrHistoricalData
from apps.predictor.services import TrainingService


class Command(BaseCommand):
    help = "Fetch USD/IDR historical data from Yahoo Finance and seed the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--years", type=int, default=10, help="Years of data to fetch"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Print without inserting"
        )

    def handle(self, *args, **options):
        years = options["years"]
        dry_run = options["dry_run"]

        self.stdout.write(f"Fetching IDR=X data for {years} years...")
        try:
            df = TrainingService.fetch_usdidr(years=years)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Fetch failed: {e}"))
            return

        self.stdout.write(f"Fetched {len(df)} rows.")

        if dry_run:
            for _, row in df.head().iterrows():
                self.stdout.write(f"  {row['ds'].date()}: {row['y']:.2f}")
            self.stdout.write(f"Total: {len(df)} rows")
            return

        inserted = 0
        updated = 0
        for _, row in df.iterrows():
            obj, created = UsdIdrHistoricalData.objects.update_or_create(
                date=row["ds"].date(),
                defaults={"close": round(float(row["y"]), 2)},
            )
            if created:
                inserted += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Done. Inserted: {inserted}, Updated: {updated}")
        )
