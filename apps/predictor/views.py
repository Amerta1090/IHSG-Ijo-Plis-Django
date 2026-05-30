import json
from datetime import date

from django.shortcuts import render

from apps.predictor.models import HistoricalData, ModelVersion, PredictionResult


def index(request):
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

    context = {
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
    }

    return render(request, "index.html", context)
