import json
from datetime import date, timedelta

from django.http import JsonResponse
from django.shortcuts import render

from apps.predictor.models import (
    HistoricalData,
    ModelVersion,
    PredictionResult,
    UsdIdrHistoricalData,
    UsdIdrPredictionResult,
)
from apps.predictor.services import PredictionService

MARKET_CONFIG = {
    "ihsg": {
        "name": "IHSG",
        "title": "Dashboard — IHSG Predictor",
        "symbol": "^JKSE",
        "historical_model": HistoricalData,
        "prediction_model": PredictionResult,
        "nowLabel": "IHSG Now",
        "histLabel": "IHSG Historical",
        "fullName": "IHSG Predictor",
        "apiEndpoint": "/api/metrics.json",
        "decompEndpoint": "/api/decomposition.json",
        "colors": {
            "historical": "#22c55e",
            "historical_fill": "rgba(34, 197, 94, 0.12)",
            "prediction": "#f59e0b",
            "band": "rgba(245, 158, 11, 0.1)",
        },
        "metric_suffix": "",
    },
    "usdidr": {
        "name": "USD/IDR",
        "title": "Dashboard — USD/IDR Predictor",
        "symbol": "USDIDR=X",
        "historical_model": UsdIdrHistoricalData,
        "prediction_model": UsdIdrPredictionResult,
        "nowLabel": "Kurs Now",
        "histLabel": "USD/IDR Historical",
        "fullName": "USD/IDR Predictor",
        "apiEndpoint": "/api/usdidr/metrics.json",
        "decompEndpoint": "/api/usdidr/decomposition.json",
        "colors": {
            "historical": "#3b82f6",
            "historical_fill": "rgba(59, 130, 246, 0.12)",
            "prediction": "#f59e0b",
            "band": "rgba(245, 158, 11, 0.1)",
        },
        "metric_suffix": "",
    },
}


def _compute_sma(historical_data, window):
    if len(historical_data) < window:
        return []
    values = [d["close"] for d in historical_data]
    sma = []
    for i in range(len(values)):
        if i < window - 1:
            continue
        avg = sum(values[i - window + 1 : i + 1]) / window
        sma.append({"date": historical_data[i]["date"], "value": round(avg, 2)})
    return sma


def _compute_volatility(historical_data, window=20):
    if len(historical_data) < window + 1:
        return None
    closes = [d["close"] for d in historical_data[-window - 1 :]]
    returns = [
        (closes[i] - closes[i - 1]) / closes[i - 1] * 100 for i in range(1, len(closes))
    ]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / len(returns)
    std = variance**0.5
    return round(std, 2)


def _get_dashboard_data(market="ihsg", request=None):
    cfg = MARKET_CONFIG[market]
    hist_model = cfg["historical_model"]
    pred_model = cfg["prediction_model"]

    historical_qs = hist_model.objects.all().order_by("date")
    historical_data = [{"date": str(h.date), "close": h.close} for h in historical_qs]

    pred_version = None
    active_model = None
    if market == "ihsg":
        active_model = ModelVersion.objects.filter(is_active=True).first()
        if (
            active_model
            and pred_model.objects.filter(
                model_version=active_model.version
            ).exists()
        ):
            pred_version = active_model.version
        else:
            latest = (
                pred_model.objects.values_list("model_version", flat=True)
                .distinct()
                .order_by("-model_version")
                .first()
            )
            pred_version = latest
    else:
        latest = (
            pred_model.objects.values_list("model_version", flat=True)
            .distinct()
            .order_by("-model_version")
            .first()
        )
        pred_version = latest

    prediction_data = []
    if pred_version:
        preds = pred_model.objects.filter(model_version=pred_version).order_by("date")
        last_hist_date = (
            historical_qs.last().date if historical_qs.exists() else date.min
        )
        for p in preds:
            if p.date > last_hist_date and p.yhat > 0:
                prediction_data.append(
                    {
                        "date": str(p.date),
                        "yhat": p.yhat,
                        "yhat_lower": p.yhat_lower,
                        "yhat_upper": p.yhat_upper,
                    }
                )

    market_now = historical_qs.last()
    market_prev = (
        historical_qs.order_by("-date")[1] if historical_qs.count() > 1 else None
    )

    change_pct = 0.0
    change_value = 0.0
    if market_now and market_prev and market_prev.close:
        change_value = round(market_now.close - market_prev.close, 2)
        change_pct = round((change_value / market_prev.close) * 100, 2)

    week_ago = historical_qs.order_by("-date")[4] if historical_qs.count() > 5 else None
    week_change_pct = 0.0
    week_change_value = 0.0
    if market_now and week_ago and week_ago.close:
        week_change_value = round(market_now.close - week_ago.close, 2)
        week_change_pct = round((week_change_value / week_ago.close) * 100, 2)

    prediksi_30d = None
    if len(prediction_data) >= 30:
        prediksi_30d = round(prediction_data[29]["yhat"], 2)
    elif prediction_data:
        prediksi_30d = round(prediction_data[-1]["yhat"], 2)

    confidence_score = 0
    if prediction_data:
        widths = [
            p["yhat_upper"] - p["yhat_lower"]
            for p in prediction_data
            if p["yhat_upper"] > p["yhat_lower"]
        ]
        if widths:
            avg_width = sum(widths) / len(widths)
            confidence_score = round(max(0, min(100, 100 - (avg_width / 15))))

    sentiment = "Neutral"
    if len(prediction_data) >= 2:
        first_val = prediction_data[0]["yhat"]
        last_val = prediction_data[-1]["yhat"]
        slope_pct = ((last_val - first_val) / first_val) * 100 if first_val else 0
        if slope_pct > 2:
            sentiment = "Bullish"
        elif slope_pct < -2:
            sentiment = "Bearish"

    last_updated = (
        active_model.trained_at.strftime("%Y-%m-%d %H:%M:%S")
        if active_model
        else (pred_version if pred_version else None)
    )

    data_status = "no_data"
    today = date.today()
    if historical_qs.exists():
        last_hist_date = historical_qs.last().date
        if last_hist_date == today:
            data_status = "today"
        elif last_hist_date == today - timedelta(days=1):
            data_status = "yesterday"
        else:
            data_status = "stale"

    sma_20 = _compute_sma(historical_data, 20)
    sma_50 = _compute_sma(historical_data, 50)
    volatility = _compute_volatility(historical_data, 20)

    pred_vs_actual = []
    if pred_version:
        actual_map = {h.date: h.close for h in historical_qs}
        preds = pred_model.objects.filter(model_version=pred_version).order_by("date")
        for p in preds:
            actual = actual_map.get(p.date)
            if actual is not None:
                pred_vs_actual.append(
                    {
                        "date": str(p.date),
                        "predicted": round(p.yhat, 2),
                        "actual": actual,
                        "error_pct": round(abs(p.yhat - actual) / actual * 100, 2),
                    }
                )

    context = {
        "historical_json": json.dumps(historical_data),
        "predictions_json": json.dumps(prediction_data),
        "market_now": market_now.close if market_now else None,
        "change_pct": change_pct,
        "change_value": change_value,
        "week_change_pct": week_change_pct,
        "week_change_value": week_change_value,
        "prediksi_30d": prediksi_30d,
        "confidence_score": confidence_score,
        "sentiment": sentiment,
        "last_updated": last_updated,
        "active_model_version": active_model.version if active_model else None,
        "historical_count": historical_qs.count(),
        "prediction_count": len(prediction_data),
        "sma_20_json": json.dumps(sma_20),
        "sma_50_json": json.dumps(sma_50),
        "volatility": volatility,
        "pred_vs_actual": pred_vs_actual,
        "pred_vs_actual_json": json.dumps(pred_vs_actual),
        "data_status": data_status,
        "market": cfg,
        "market_json": json.dumps(
            {k: v for k, v in cfg.items()
             if k not in ("historical_model", "prediction_model")}
        ),
    }
    return context


def dashboard(request, market="ihsg"):
    try:
        context = _get_dashboard_data(market, request)
    except Exception:
        cfg = MARKET_CONFIG.get(market, MARKET_CONFIG["ihsg"])
        context = {
            "historical_json": "[]",
            "predictions_json": "[]",
            "market_now": None,
            "change_pct": 0,
            "change_value": 0,
            "week_change_pct": 0,
            "week_change_value": 0,
            "prediksi_30d": None,
            "confidence_score": 0,
            "sentiment": "Neutral",
            "last_updated": None,
            "active_model_version": None,
            "historical_count": 0,
            "prediction_count": 0,
            "sma_20_json": "[]",
            "sma_50_json": "[]",
            "volatility": None,
            "pred_vs_actual": [],
            "pred_vs_actual_json": "[]",
            "data_status": "no_data",
            "market": cfg,
            "market_json": json.dumps(
                {k: v for k, v in cfg.items()
                 if k not in ("historical_model", "prediction_model")}
            ),
            "error": "Data sedang tidak tersedia. Silakan coba lagi nanti.",
        }
    return render(request, "dashboard.html", context)


def index(request):
    return dashboard(request, market="ihsg")


def about(request):
    try:
        model_versions = list(ModelVersion.objects.all().order_by("-trained_at"))
        historical_count = HistoricalData.objects.count()
        active_model_obj = ModelVersion.objects.filter(is_active=True).first()

        model_stats = []
        for mv in model_versions:
            model_stats.append(
                {
                    "version": mv.version,
                    "trained_at": mv.trained_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "data_end_date": str(mv.data_end_date),
                    "mae": mv.metrics.get("mae"),
                    "rmse": mv.metrics.get("rmse"),
                    "is_active": mv.is_active,
                }
            )

        active_stats = None
        if active_model_obj:
            active_stats = {
                "version": active_model_obj.version,
                "trained_at": active_model_obj.trained_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "data_end_date": str(active_model_obj.data_end_date),
                "mae": active_model_obj.metrics.get("mae"),
                "rmse": active_model_obj.metrics.get("rmse"),
                "is_active": True,
            }

        context = {
            "model_stats": model_stats,
            "active_model": active_stats,
            "historical_count": historical_count,
            "model_count": len(model_versions),
            "model_stats_json": json.dumps(model_stats),
        }
    except Exception:
        context = {
            "model_stats": [],
            "active_model": None,
            "historical_count": 0,
            "model_count": 0,
            "model_stats_json": "[]",
        }
    return render(request, "about.html", context)


def metrics_api(request):
    try:
        data = _get_dashboard_data("ihsg", request)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    json_data = {
        "historical": json.loads(data["historical_json"]),
        "predictions": json.loads(data["predictions_json"]),
        "market_now": data["market_now"],
        "change_pct": data["change_pct"],
        "change_value": data["change_value"],
        "week_change_pct": data["week_change_pct"],
        "week_change_value": data["week_change_value"],
        "prediksi_30d": data["prediksi_30d"],
        "confidence_score": data["confidence_score"],
        "sentiment": data["sentiment"],
        "last_updated": data["last_updated"],
        "active_model_version": data["active_model_version"],
        "sma_20": json.loads(data["sma_20_json"]),
        "sma_50": json.loads(data["sma_50_json"]),
        "volatility": data["volatility"],
        "pred_vs_actual": json.loads(data["pred_vs_actual_json"]),
        "data_status": data["data_status"],
    }
    return JsonResponse(json_data)


def usdidr_metrics_api(request):
    try:
        data = _get_dashboard_data("usdidr", request)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    json_data = {
        "historical": json.loads(data["historical_json"]),
        "predictions": json.loads(data["predictions_json"]),
        "market_now": data["market_now"],
        "change_pct": data["change_pct"],
        "change_value": data["change_value"],
        "week_change_pct": data["week_change_pct"],
        "week_change_value": data["week_change_value"],
        "prediksi_30d": data["prediksi_30d"],
        "confidence_score": data["confidence_score"],
        "sentiment": data["sentiment"],
        "last_updated": data["last_updated"],
        "active_model_version": data["active_model_version"],
        "sma_20": json.loads(data["sma_20_json"]),
        "sma_50": json.loads(data["sma_50_json"]),
        "volatility": data["volatility"],
        "pred_vs_actual": json.loads(data["pred_vs_actual_json"]),
        "data_status": data["data_status"],
    }
    return JsonResponse(json_data)


def decomposition_api(request):
    try:
        model = PredictionService.load_model()
        historical = HistoricalData.objects.all().order_by("date")
        start_date = historical.first().date if historical.exists() else None
        end_date = historical.last().date if historical.exists() else None
        if not start_date or not end_date:
            return JsonResponse({"error": "No historical data"}, status=404)

        future = model.make_future_dataframe(periods=0, include_history=True)
        forecast = model.predict(future)
        forecast["ds"] = forecast["ds"].dt.strftime("%Y-%m-%d")

        result = {
            "trend": forecast[["ds", "trend"]]
            .rename(columns={"trend": "value"})
            .to_dict(orient="records"),
        }

        if "weekly" in forecast.columns:
            result["weekly"] = (
                forecast[["ds", "weekly"]]
                .rename(columns={"weekly": "value"})
                .to_dict(orient="records")
            )
        else:
            result["weekly"] = []

        if "yearly" in forecast.columns:
            result["yearly"] = (
                forecast[["ds", "yearly"]]
                .rename(columns={"yearly": "value"})
                .to_dict(orient="records")
            )
        else:
            result["yearly"] = []

        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def usdidr_decomposition_api(request):
    try:
        model = PredictionService.load_model(market="usdidr")
        historical = UsdIdrHistoricalData.objects.all().order_by("date")
        start_date = historical.first().date if historical.exists() else None
        end_date = historical.last().date if historical.exists() else None
        if not start_date or not end_date:
            return JsonResponse({"error": "No historical data"}, status=404)

        future = model.make_future_dataframe(periods=0, include_history=True)
        forecast = model.predict(future)
        forecast["ds"] = forecast["ds"].dt.strftime("%Y-%m-%d")

        result = {
            "trend": forecast[["ds", "trend"]]
            .rename(columns={"trend": "value"})
            .to_dict(orient="records"),
        }

        if "weekly" in forecast.columns:
            result["weekly"] = (
                forecast[["ds", "weekly"]]
                .rename(columns={"weekly": "value"})
                .to_dict(orient="records")
            )
        else:
            result["weekly"] = []

        if "yearly" in forecast.columns:
            result["yearly"] = (
                forecast[["ds", "yearly"]]
                .rename(columns={"yearly": "value"})
                .to_dict(orient="records")
            )
        else:
            result["yearly"] = []

        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
