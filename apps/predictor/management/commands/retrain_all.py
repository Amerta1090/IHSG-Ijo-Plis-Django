import logging
from datetime import datetime

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.predictor.models import (
    ModelVersion,
    PredictionResult,
    UsdIdrHistoricalData,
    UsdIdrPredictionResult,
)
from apps.predictor.services import PredictionService, TrainingService

logger = logging.getLogger(__name__)


def _retrain_market(market: str) -> str | None:
    from apps.predictor.models import HistoricalData

    if market == "ihsg":
        hist_model = HistoricalData
        pred_model = PredictionResult
        fetch_fn = TrainingService.fetch_ihsg
        model_market = "ihsg"
    elif market == "usdidr":
        hist_model = UsdIdrHistoricalData
        pred_model = UsdIdrPredictionResult
        fetch_fn = TrainingService.fetch_usdidr
        model_market = "usdidr"
    else:
        raise ValueError(f"Unknown market: {market}")

    logger.info("Step 1: Fetching %s data...", market)
    df = fetch_fn(years=10)

    inserted = 0
    updated = 0
    for _, row in df.iterrows():
        obj, created = hist_model.objects.update_or_create(
            date=row["ds"].date(),
            defaults={"close": round(float(row["y"]), 2)},
        )
        if created:
            inserted += 1
        else:
            updated += 1
    logger.info("DB updated: %d new, %d existing", inserted, updated)

    qs = hist_model.objects.all().order_by("date")
    hist_df = pd.DataFrame(list(qs.values("date", "close"))).rename(
        columns={"date": "ds", "close": "y"}
    )
    data_end = hist_df["ds"].max()

    logger.info("Step 2: Training Prophet on %d rows...", len(hist_df))
    model = TrainingService.train_prophet(hist_df)

    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    TrainingService.save_model(model, version, market=model_market)
    metrics = TrainingService.evaluate(model, hist_df)
    logger.info("Model v%s metrics: %s", version, metrics)

    if market == "ihsg":
        ModelVersion.objects.create(
            version=version,
            trained_at=datetime.now(),
            data_end_date=data_end,
            metrics=metrics,
            is_active=False,
        )
        ModelVersion.set_best_active()
        best = ModelVersion.objects.filter(is_active=True).first()
        if best:
            mae = best.metrics.get("mae")
            logger.info("Best model: v%s (MAE=%s)", best.version, mae)

    logger.info("Step 3: Generating predictions...")
    PredictionService._models[model_market] = model
    result = PredictionService.predict(periods=90, market=model_market)

    with transaction.atomic():
        for row in result:
            pred_model.objects.update_or_create(
                date=row["ds"].date(),
                model_version=version,
                defaults={
                    "yhat": round(float(row["yhat"]), 2),
                    "yhat_lower": round(float(row["yhat_lower"]), 2),
                    "yhat_upper": round(float(row["yhat_upper"]), 2),
                },
            )

    logger.info("%s retrain complete. v%s", market.upper(), version)
    return version


class Command(BaseCommand):
    help = "Full retrain pipeline for both IHSG and USD/IDR without Celery"

    def handle(self, *args, **options):
        self.stdout.write("Starting full retrain pipeline (IHSG + USD/IDR)...")

        try:
            ihsg_version = _retrain_market("ihsg")
            self.stdout.write(
                self.style.SUCCESS(f"IHSG retrain complete: v{ihsg_version}")
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"IHSG retrain failed: {e}"))

        try:
            usdidr_version = _retrain_market("usdidr")
            self.stdout.write(
                self.style.SUCCESS(f"USD/IDR retrain complete: v{usdidr_version}")
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"USD/IDR retrain failed: {e}"))

        self.stdout.write(self.style.SUCCESS("Full retrain pipeline finished."))
