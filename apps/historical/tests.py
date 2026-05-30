import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .models import HistoricalData, UploadedCSV
from .services import bulk_insert, parse_csv

TEMP_MEDIA = tempfile.mkdtemp()


class HistoricalDataModelTest(TestCase):
    def test_create_historical_data(self):
        record = HistoricalData.objects.create(
            date="2024-01-15",
            close=7200.50,
            source="manual",
        )
        self.assertEqual(str(record.date), "2024-01-15")
        self.assertEqual(record.close, 7200.50)
        self.assertEqual(record.source, "manual")
        self.assertEqual(str(record), "2024-01-15: 7200.5")

    def test_unique_date_constraint(self):
        HistoricalData.objects.create(date="2024-01-15", close=7200.50)
        with self.assertRaises(Exception):
            HistoricalData.objects.create(date="2024-01-15", close=7300.00)

    def test_default_ordering(self):
        HistoricalData.objects.create(date="2024-01-15", close=7200)
        HistoricalData.objects.create(date="2024-01-14", close=7100)
        qs = HistoricalData.objects.all()
        self.assertEqual(str(qs[0].date), "2024-01-15")
        self.assertEqual(str(qs[1].date), "2024-01-14")


class UploadedCSVModelTest(TestCase):
    def test_create_uploaded_csv(self):
        csv_file = SimpleUploadedFile("test.csv", b"ds,y\n2024-01-01,7000")
        record = UploadedCSV.objects.create(file=csv_file)
        self.assertEqual(record.status, "pending")
        self.assertIn("csv_uploads/", str(record))
        self.assertIn("pending", str(record))


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class CSVParserTest(TestCase):
    def test_valid_csv(self):
        content = b"ds,y\n2024-01-01,7000\n2024-01-02,7100\n"
        file = SimpleUploadedFile("valid.csv", content)
        rows, errors = parse_csv(file)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(rows), 2)
        self.assertEqual(str(rows[0]["date"]), "2024-01-01")
        self.assertEqual(rows[0]["close"], 7000.0)

    def test_missing_columns(self):
        content = b"date,price\n2024-01-01,7000\n"
        file = SimpleUploadedFile("bad.csv", content)
        rows, errors = parse_csv(file)
        self.assertEqual(len(rows), 0)
        self.assertTrue(len(errors) > 0)
        self.assertTrue("ds" in errors[0] or "y" in errors[0])

    def test_invalid_close_price(self):
        content = b"ds,y\n2024-01-01,-100\n"
        file = SimpleUploadedFile("neg.csv", content)
        rows, errors = parse_csv(file)
        self.assertEqual(len(rows), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("positive", errors[0])

    def test_empty_file(self):
        content = b"ds,y\n"
        file = SimpleUploadedFile("empty.csv", content)
        rows, errors = parse_csv(file)
        self.assertEqual(len(rows), 0)
        self.assertEqual(len(errors), 0)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class BulkInsertTest(TestCase):
    def test_bulk_insert_new(self):
        rows = [
            {"date": "2024-01-01", "close": 7000.0},
            {"date": "2024-01-02", "close": 7100.0},
        ]
        inserted = bulk_insert(rows)
        self.assertEqual(inserted, 2)
        self.assertEqual(HistoricalData.objects.count(), 2)

    def test_bulk_insert_duplicate(self):
        HistoricalData.objects.create(date="2024-01-01", close=7000)
        rows = [
            {"date": "2024-01-01", "close": 7050.0},
            {"date": "2024-01-02", "close": 7100.0},
        ]
        inserted = bulk_insert(rows)
        self.assertEqual(inserted, 1)
        self.assertEqual(HistoricalData.objects.count(), 2)
        self.assertEqual(HistoricalData.objects.get(date="2024-01-01").close, 7050.0)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class UploadFlowIntegrationTest(TestCase):
    def test_upload_csv_end_to_end(self):
        from apps.historical.models import UploadedCSV
        from apps.historical.services import bulk_insert, parse_csv

        csv_file = SimpleUploadedFile(
            "test.csv",
            b"ds,y\n2024-01-01,7000\n2024-01-02,7100\n",
        )
        uploaded = UploadedCSV.objects.create(file=csv_file)
        rows, errors = parse_csv(uploaded.file)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(rows), 2)

        inserted = bulk_insert(rows)
        self.assertEqual(inserted, 2)

        uploaded.status = "done"
        uploaded.save()
        uploaded.refresh_from_db()
        self.assertEqual(uploaded.status, "done")

    def test_seed_command_parse(self):
        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command("seed_ihsg", dry_run=True, years=1, stdout=out)
        output = out.getvalue()
        self.assertIn("Fetching IHSG", output)
