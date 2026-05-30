import io
import logging

import pandas as pd
from django.core.files.uploadedfile import UploadedFile

from .models import HistoricalData, UploadedCSV

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"ds", "y"}


def parse_csv(file: UploadedFile) -> tuple[list[dict], list[str]]:
    df = pd.read_csv(io.BytesIO(file.read()))
    file.seek(0)

    columns = set(df.columns.str.strip().str.lower())
    missing = REQUIRED_COLUMNS - columns
    if missing:
        return [], [f"Missing required columns: {', '.join(sorted(missing))}"]

    ds_col = next(c for c in df.columns if c.strip().lower() == "ds")
    y_col = next(c for c in df.columns if c.strip().lower() == "y")

    errors: list[str] = []
    rows: list[dict] = []

    for idx, row in df.iterrows():
        try:
            date = pd.Timestamp(row[ds_col])
            close = float(row[y_col])
        except (ValueError, TypeError):
            ds_val = row.get(ds_col, "?")
            y_val = row.get(y_col, "?")
            errors.append(f"Row {idx + 2}: invalid data (ds={ds_val}, y={y_val})")
            continue

        if close <= 0:
            errors.append(f"Row {idx + 2}: close price must be positive (got {close})")
            continue

        rows.append({"date": date.date(), "close": close})

    return rows, errors


def bulk_insert(rows: list[dict], source: str = "csv") -> int:
    inserted = 0
    for row in rows:
        _, created = HistoricalData.objects.update_or_create(
            date=row["date"],
            defaults={"close": row["close"], "source": source},
        )
        if created:
            inserted += 1
    return inserted


def process_uploaded_csv(uploaded: UploadedCSV) -> tuple[int, int, list[str]]:
    rows, errors = parse_csv(uploaded.file)
    if errors:
        uploaded.status = "error"
        uploaded.save()
        return 0, 0, errors

    inserted = bulk_insert(rows)
    uploaded.status = "done"
    uploaded.save()
    return len(rows), inserted, errors
