from datetime import date

from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.predictor.models import (
    UsdIdrHistoricalData,
    UsdIdrPredictionResult,
)


class UsdIdrModelsTest(TestCase):
    def test_create_historical_data(self):
        obj = UsdIdrHistoricalData.objects.create(
            date=date(2026, 1, 2),
            close=16250.00,
        )
        self.assertEqual(str(obj), "2026-01-02: 16250.0")
        self.assertEqual(obj.close, 16250.00)

    def test_prediction_result_unique_together(self):
        UsdIdrPredictionResult.objects.create(
            date=date(2026, 6, 1),
            yhat=16300.00,
            yhat_lower=16200.00,
            yhat_upper=16400.00,
            model_version="v1",
        )
        with self.assertRaises(Exception):
            UsdIdrPredictionResult.objects.create(
                date=date(2026, 6, 1),
                yhat=16350.00,
                yhat_lower=16250.00,
                yhat_upper=16450.00,
                model_version="v1",
            )


class UsdIdrDashboardTest(TestCase):
    @override_settings(DEBUG=True)
    def test_dashboard_renders(self):
        response = self.client.get("/usdidr/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")
        self.assertIn("market", response.context)
        self.assertEqual(response.context["market"]["name"], "USD/IDR")

    def test_dashboard_empty_state(self):
        response = self.client.get("/usdidr/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["historical_count"], 0)
        self.assertEqual(response.context["prediction_count"], 0)

    def test_dashboard_with_data(self):
        UsdIdrHistoricalData.objects.create(date=date(2026, 5, 1), close=16000.00)
        UsdIdrHistoricalData.objects.create(date=date(2026, 5, 2), close=16100.00)
        UsdIdrPredictionResult.objects.create(
            date=date(2026, 6, 1),
            yhat=16200.00,
            yhat_lower=16100.00,
            yhat_upper=16300.00,
            model_version="test_v1",
        )
        UsdIdrPredictionResult.objects.create(
            date=date(2026, 6, 2),
            yhat=16300.00,
            yhat_lower=16200.00,
            yhat_upper=16400.00,
            model_version="test_v1",
        )
        response = self.client.get("/usdidr/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["historical_count"], 2)
        self.assertIn("2026-05-01", response.context["historical_json"])


class UsdIdrApiTest(TestCase):
    def test_metrics_api_returns_json(self):
        response = self.client.get("/api/usdidr/metrics.json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("historical", data)
        self.assertIn("predictions", data)
        self.assertIn("market_now", data)

    def test_decomposition_api_without_data(self):
        response = self.client.get("/api/usdidr/decomposition.json")
        self.assertEqual(response.status_code, 404)


class UsdIdrPredictionCommandTest(TestCase):
    def test_predict_command_no_model(self):
        from io import StringIO

        out = StringIO()
        err = StringIO()
        call_command("predict_usdidr", "--periods", "5", stdout=out, stderr=err)
        output = out.getvalue()
        self.assertIn("predict", output.lower())


class AboutPageTest(TestCase):
    def test_about_renders(self):
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "about.html")
        self.assertIn("usdidr_historical_count", response.context)
        self.assertIn("usdidr_model_version", response.context)
