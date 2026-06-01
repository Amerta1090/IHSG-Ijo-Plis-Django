import logging
from datetime import datetime

import pandas as pd
from celery import shared_task
from django.db import transaction

from apps.predictor.models import HistoricalData, ModelVersion, PredictionResult
from apps.predictor.services import PredictionService, TrainingService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def retrain_pipeline(self):
    """Full retrain pipeline: fetch → train → predict."""
    logger.info("Starting retrain pipeline...")

    # Step 1: Fetch
    logger.info("Fetching IHSG data...")
    try:
        df = TrainingService.fetch_ihsg(years=10)
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        raise self.retry(exc=e, countdown=300)

    # Step 2: Store in DB
    inserted = 0
    updated = 0
    for _, row in df.iterrows():
        obj, created = HistoricalData.objects.update_or_create(
            date=row["ds"].date(),
            defaults={"close": round(float(row["y"]), 2)},
        )
        if created:
            inserted += 1
        else:
            updated += 1
    logger.info(f"DB updated: {inserted} new, {updated} existing")

    # Step 3: Train Prophet
    qs = HistoricalData.objects.all().order_by("date")
    hist_df = pd.DataFrame(list(qs.values("date", "close"))).rename(
        columns={"date": "ds", "close": "y"}
    )
    data_end = hist_df["ds"].max()

    logger.info(f"Training Prophet on {len(hist_df)} rows...")
    try:
        model = TrainingService.train_prophet(hist_df)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise self.retry(exc=e, countdown=300)

    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    TrainingService.save_model(model, version)
    metrics = TrainingService.evaluate(model, hist_df)
    logger.info(f"Model v{version} metrics: {metrics}")

    ModelVersion.objects.create(
        version=version,
        trained_at=datetime.now(),
        data_end_date=data_end,
        metrics=metrics,
        is_active=False,
    )
    ModelVersion.set_best_active()
    best = ModelVersion.objects.filter(is_active=True).first()
    logger.info(f"Best model: v{best.version} (MAE={best.metrics.get('mae', 'N/A')})")

    # Step 4: Predict
    logger.info("Generating predictions...")
    PredictionService._model = model
    try:
        result = PredictionService.predict(periods=90)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return

    with transaction.atomic():
        for row in result:
            PredictionResult.objects.update_or_create(
                date=row["ds"].date(),
                model_version=version,
                defaults={
                    "yhat": round(float(row["yhat"]), 2),
                    "yhat_lower": round(float(row["yhat_lower"]), 2),
                    "yhat_upper": round(float(row["yhat_upper"]), 2),
                },
            )

    logger.info(f"Retrain pipeline complete. v{version}")
