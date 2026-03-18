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

    # Normalize common invisible characters that often appear in CSV exports
    s = (
        s.replace("\ufeff", "")   # BOM
         .replace("\u00a0", " ")  # non-breaking space
         .replace("\u200b", "")   # zero-width space
         .replace("\u200c", "")   # zero-width non-joiner
         .replace("\u200d", "")   # zero-width joiner
         .replace("\u2060", "")   # word joiner
    )

    s = s.strip()
    return s if s != "" else None


def _to_int(s: Optional[str]) -> Optional[int]:
    s = _clean(s)
    if s is None:
        return None
    try:
        return int(s)
    except ValueError as e:
        raise ValueError(f"Invalid int value: {s!r}") from e


def _to_float(s: Optional[str]) -> Optional[float]:
    s = _clean(s)
    if s is None:
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError as e:
        raise ValueError(f"Invalid float value: {s!r}") from e


def _parse_date(s: Optional[str]) -> datetime:
    s = _clean(s)
    if s is None:
        raise ValueError("Missing required field: 'date'")

    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass

    raise ValueError(f"Invalid date format for 'date': {s!r} (expected YYYY-MM-DD or DD/MM/YYYY)")


def _normalize_header(name: str) -> str:
    name = name.strip()
    return name.lstrip("\ufeff")


def _is_effectively_empty_row(row: dict) -> bool:
    """
    A row is considered empty if all its values are empty/whitespace/invisible chars.
    Also handles extra unnamed columns that DictReader can place under key None.
    """
    for key, value in row.items():
        if key is None:
            # Extra columns can appear here as a list
            if isinstance(value, list):
                for item in value:
                    if _clean(item) is not None:
                        return False
            else:
                if _clean(value) is not None:
                    return False
        else:
            if _clean(value) is not None:
                return False

    return True


class DI_CsvParserV1(CSVParser_Interface):
    def parse(self, file_bytes: bytes) -> list[DailyMetricsInput]:
        try:
            decoded = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError as e:
            raise ValueError("CSV must be UTF-8 encoded.") from e

        sample = decoded[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=";,")
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ";"

        reader = csv.DictReader(StringIO(decoded), delimiter=delimiter)

        if reader.fieldnames is None:
            raise ValueError("CSV appears to have no header row.")

        normalized_fieldnames = [_normalize_header(h) for h in reader.fieldnames]
        key_map = {old: new for old, new in zip(reader.fieldnames, normalized_fieldnames)}

        if "date" not in normalized_fieldnames:
            raise ValueError("CSV header must include required column: 'date'")

        parsed: list[DailyMetricsInput] = []

        for row_idx, raw_row in enumerate(reader, start=2):
            row = {key_map.get(k, k): v for k, v in raw_row.items()}

            # Skip rows that are effectively blank
            if _is_effectively_empty_row(row):
                continue

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
                raise ValueError(f"CSV parse error on row {row_idx}: {e}") from e

            parsed.append(entity)

        return parsed