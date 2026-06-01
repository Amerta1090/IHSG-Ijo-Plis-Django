import json
from datetime import date

from django.http import JsonResponse
from django.shortcuts import render

from apps.predictor.models import HistoricalData, ModelVersion, PredictionResult
from apps.predictor.services import PredictionService


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
        (closes[i] - closes[i - 1]) / closes[i - 1] * 100
        for i in range(1, len(closes))
    ]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / len(returns)
    std = variance ** 0.5
    return round(std, 2)


def _get_dashboard_data(request=None):
    historical_qs = HistoricalData.objects.all().order_by("date")
    historical_data = [
        {"date": str(h.date), "close": h.close} for h in historical_qs
    ]

    active_model = ModelVersion.objects.filter(is_active=True).first()
    pred_version = None
    if active_model and PredictionResult.objects.filter(
        model_version=active_model.version
    ).exists():
        pred_version = active_model.version
    else:
        latest = (
            PredictionResult.objects.values_list("model_version", flat=True)
            .distinct()
            .order_by("-model_version")
            .first()
        )
        pred_version = latest

    prediction_data = []
    if pred_version:
        preds = PredictionResult.objects.filter(
            model_version=pred_version
        ).order_by("date")
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

    ihsg_now = historical_qs.last()
    ihsg_prev = (
        historical_qs.order_by("-date")[1] if historical_qs.count() > 1 else None
    )

    change_pct = 0.0
    change_value = 0.0
    if ihsg_now and ihsg_prev and ihsg_prev.close:
        change_value = round(ihsg_now.close - ihsg_prev.close, 2)
        change_pct = round((change_value / ihsg_prev.close) * 100, 2)

    week_ago = (
        historical_qs.order_by("-date")[4] if historical_qs.count() > 5 else None
    )
    week_change_pct = 0.0
    week_change_value = 0.0
    if ihsg_now and week_ago and week_ago.close:
        week_change_value = round(ihsg_now.close - week_ago.close, 2)
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
        active_model.trained_at.strftime("%Y-%m-%d %H:%M:%S") if active_model else None
    )

    sma_20 = _compute_sma(historical_data, 20)
    sma_50 = _compute_sma(historical_data, 50)
    volatility = _compute_volatility(historical_data, 20)

    pred_vs_actual = []
    if pred_version:
        actual_map = {h.date: h.close for h in historical_qs}
        preds = PredictionResult.objects.filter(
            model_version=pred_version
        ).order_by("date")
        for p in preds:
            actual = actual_map.get(p.date)
            if actual is not None:
                pred_vs_actual.append(
                    {
                        "date": str(p.date),
                        "predicted": round(p.yhat, 2),
                        "actual": actual,
                        "error_pct": round(
                            abs(p.yhat - actual) / actual * 100, 2
                        ),
                    }
                )

    return {
        "historical_json": json.dumps(historical_data),
        "predictions_json": json.dumps(prediction_data),
        "ihsg_now": ihsg_now.close if ihsg_now else None,
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
    }


def index(request):
    try:
        context = _get_dashboard_data(request)
    except Exception:
        context = {
            "historical_json": "[]",
            "predictions_json": "[]",
            "ihsg_now": None,
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
            "error": "Data sedang tidak tersedia. Silakan coba lagi nanti.",
        }
    return render(request, "index.html", context)


def about(request):
    model_versions = list(ModelVersion.objects.all().order_by("-trained_at"))
    historical_count = HistoricalData.objects.count()

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

    active_stats = model_stats[0] if model_stats else None

    context = {
        "model_stats": model_stats,
        "active_model": active_stats,
        "historical_count": historical_count,
        "model_count": len(model_versions),
        "model_stats_json": json.dumps(model_stats),
    }
    return render(request, "about.html", context)


def metrics_api(request):
    try:
        data = _get_dashboard_data(request)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    json_data = {
        "historical": json.loads(data["historical_json"]),
        "predictions": json.loads(data["predictions_json"]),
        "ihsg_now": data["ihsg_now"],
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
