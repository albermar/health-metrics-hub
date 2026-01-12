# app/infrastructure/parser/parser_impls.py

from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from typing import Optional

from app.domain.entities import DailyMetricsInput
from app.domain.interfaces import CSVParser_Interface


def _clean(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    return s if s != "" else None


def _to_int(s: Optional[str]) -> Optional[int]:
    s = _clean(s)
    if s is None:
        return None
    try:
        return int(s)
    except ValueError:
        # You can choose to raise instead. For now: fail fast with a clear error.
        raise ValueError(f"Invalid int value: {s!r}")


def _to_float(s: Optional[str]) -> Optional[float]:
    s = _clean(s)
    if s is None:
        return None
    try:
        return float(s)
    except ValueError:
        raise ValueError(f"Invalid float value: {s!r}")


def _parse_date(s: Optional[str]) -> datetime:
    s = _clean(s)
    if s is None:
        raise ValueError("Missing required field: 'date'")
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format for 'date': {s!r} (expected YYYY-MM-DD)")


class DI_CsvParserV1(CSVParser_Interface):
    """
    CSV -> List[DailyMetricsInput]

    Expected headers (case-sensitive):
      - date (required)
      - steps_n
      - proteins_g
      - kcal_in
      - kcal_junk_in
      - kcal_out_training
      - sleep_hours
      - stress_rel
      - weight_kg
      - waist_cm

    Notes:
      - Missing/blank optional fields become None.
      - If a column is absent, its value will also be None (because we use row.get()).
      - Invalid numbers raise ValueError with a clear message.
    """

    def parse(self, file_bytes: bytes) -> list[DailyMetricsInput]:
        # Decode
        try:
            decoded = file_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError("CSV must be UTF-8 encoded.") from e

        reader = csv.DictReader(StringIO(decoded))

        # Basic structural check: date column must exist in header
        if reader.fieldnames is None:
            raise ValueError("CSV appears to have no header row.")
        if "date" not in reader.fieldnames:
            raise ValueError("CSV header must include required column: 'date'")

        parsed: list[DailyMetricsInput] = []

        for row_idx, row in enumerate(reader, start=2):  # header is line 1
            try:
                entity = DailyMetricsInput(
                    date=_parse_date(row.get("date")),
                    steps_n=_to_int(row.get("steps_n")),
                    proteins_g=_to_int(row.get("proteins_g")),
                    kcal_in=_to_int(row.get("kcal_in")),
                    kcal_junk_in=_to_int(row.get("kcal_junk_in")),
                    kcal_out_training=_to_int(row.get("kcal_out_training")),
                    sleep_hours=_to_float(row.get("sleep_hours")),
                    stress_rel=_to_int(row.get("stress_rel")),
                    weight_kg=_to_float(row.get("weight_kg")),
                    waist_cm=_to_float(row.get("waist_cm")),
                )
            except Exception as e:
                # Attach row context for debugging (super helpful in real life)
                raise ValueError(f"CSV parse error on row {row_idx}: {e}") from e

            parsed.append(entity)

        return parsed
