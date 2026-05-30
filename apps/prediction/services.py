import logging
from pathlib import Path

import joblib
from django.conf import settings
from prophet import Prophet

logger = logging.getLogger(__name__)


class PredictionService:
    _model: Prophet | None = None

    @classmethod
    def _get_model_path(cls) -> Path:
        return settings.MEDIA_ROOT / "models" / "ihsg_prophet_model.joblib"

    @classmethod
    def load_model(cls) -> Prophet:
        if cls._model is not None:
            return cls._model

        model_path = cls._get_model_path()
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Ensure the model has been placed in media/models/"
            )

        logger.info("Loading Prophet model from %s", model_path)
        cls._model = joblib.load(model_path)
        logger.info("Model loaded successfully")
        return cls._model

    @classmethod
    def predict(cls, periods: int = 30) -> list[dict]:
        model = cls.load_model()
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)
        return result.to_dict(orient="records")
