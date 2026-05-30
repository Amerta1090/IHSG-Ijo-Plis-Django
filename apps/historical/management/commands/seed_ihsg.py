from datetime import datetime

import pandas as pd
from django.core.management.base import BaseCommand

from apps.historical.models import HistoricalData


class Command(BaseCommand):
    help = "Fetch IHSG historical data from Yahoo Finance and seed the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--years",
            type=int,
            default=5,
            help="Number of years of historical data to fetch (default: 5)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print parsed data without inserting into database",
        )

    def handle(self, *args, **options):
        years = options["years"]
        dry_run = options["dry_run"]

        end_date = datetime.now()
        start_date = end_date.replace(year=end_date.year - years)

        msg = (
            f"Fetching IHSG (^JKSE) data from {start_date.date()}"
            f" to {end_date.date()}..."
        )
        self.stdout.write(msg)

        try:
            import yfinance as yf
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    "yfinance is not installed. Run: pip install yfinance"
                )
            )
            return

        ticker = yf.Ticker("^JKSE")
        df = ticker.history(start=start_date, end=end_date)

        if df.empty:
            self.stdout.write(self.style.ERROR("No data retrieved from Yahoo Finance."))
            return

        df = df.reset_index()

        if "Date" in df.columns:
            date_col = "Date"
        elif "Datetime" in df.columns:
            date_col = "Datetime"
        else:
            cols = list(df.columns)
            self.stdout.write(self.style.ERROR(f"Unexpected columns: {cols}"))
            return

        df[date_col] = pd.to_datetime(df[date_col]).dt.tz_localize(None)
        df = df.sort_values(date_col)

        self.stdout.write(f"Fetched {len(df)} rows from Yahoo Finance.")

        if dry_run:
            self.stdout.write("\nFirst 5 rows (dry-run):")
            for _, row in df.head().iterrows():
                self.stdout.write(
                    f"  {row[date_col].strftime('%Y-%m-%d')}: {row['Close']:.2f}"
                )
            self.stdout.write(f"\nTotal rows: {len(df)}")
            return

        inserted = 0
        skipped = 0
        for _, row in df.iterrows():
            _, created = HistoricalData.objects.update_or_create(
                date=row[date_col].date(),
                defaults={
                    "close": round(float(row["Close"]), 2),
                    "source": "manual",
                },
            )
            if created:
                inserted += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Inserted: {inserted}, Updated: {skipped}, Total: {len(df)}"
            )
        )
