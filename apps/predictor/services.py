import logging
from pathlib import Path

import joblib
import pandas as pd
from django.conf import settings
from django.utils import timezone
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

    @classmethod
    def predict_from_model(cls, model: Prophet, periods: int = 90) -> pd.DataFrame:
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)


class TrainingService:
    @staticmethod
    def fetch_ihsg(years: int = 10) -> pd.DataFrame:
        import yfinance as yf

        end = timezone.now()
        start = end.replace(year=end.year - years)
        ticker = yf.Ticker("^JKSE")
        df = ticker.history(start=start, end=end)
        if df.empty:
            raise ValueError("No data retrieved from Yahoo Finance for ^JKSE")
        df = df.reset_index()
        date_col = "Date" if "Date" in df.columns else "Datetime"
        df[date_col] = pd.to_datetime(df[date_col]).dt.tz_localize(None)
        df = df.rename(columns={date_col: "ds", "Close": "y"})
        df = df[["ds", "y"]].sort_values("ds").dropna()
        return df

    @staticmethod
    def train_prophet(df: pd.DataFrame) -> Prophet:
        model = Prophet(
            growth="linear",
            seasonality_mode="multiplicative",
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        model.add_country_holidays(country_name="ID")
        model.fit(df)
        return model

    @staticmethod
    def save_model(model: Prophet, version: str) -> Path:
        models_dir = settings.MEDIA_ROOT / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        path = models_dir / f"ihsg_v{version}.joblib"
        joblib.dump(model, path)
        default_path = models_dir / "ihsg_prophet_model.joblib"
        joblib.dump(model, default_path)
        return path

    @staticmethod
    def evaluate(model: Prophet, df: pd.DataFrame) -> dict:
        forecast = model.predict(df)
        eval_df = df.copy()
        eval_df["ds"] = pd.to_datetime(eval_df["ds"])
        merged = eval_df.merge(forecast[["ds", "yhat"]], on="ds")
        mae = float((merged["y"] - merged["yhat"]).abs().mean())
        rmse = float(((merged["y"] - merged["yhat"]) ** 2).mean() ** 0.5)
        return {"mae": round(mae, 2), "rmse": round(rmse, 2)}
