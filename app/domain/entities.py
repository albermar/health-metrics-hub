from datetime import datetime
from dataclasses import dataclass
from typing import Optional # for type hinting. Optional indicates that a field can be of a certain type or None.

@dataclass
class DailyMetricsInput:
    date: datetime

    steps_n: Optional[int] = None
    proteins_g: Optional[int] = None
    
    kcal_in: Optional[int] = None
    kcal_junk_in: Optional[int] = None
    kcal_out_training: Optional[int] = None

    sleep_hours: Optional[float] = None
    stress_rel: Optional[int] = None  # 1–10 scale

    weight_kg: Optional[float] = None
    waist_cm: Optional[float] = None


@dataclass
class DailyKPIsOutput:
    """
    Minimal KPI set (8 KPIs) focused on demonstrating architecture,
    not building a huge analytics engine.
    """
    date: datetime

    # Energy / core

    kcal_out_total: Optional[float] = None
    balance_kcal: Optional[float] = None
    balance_7d_average: Optional[float] = None

    # Nutrition
    protein_per_kg: Optional[float] = None
    healthy_food_pct: Optional[float] = None

    # Activity
    adherence_steps: Optional[int] = None

    # Physiology / trend
    weight_7d_avg: Optional[float] = None
    waist_change_7d: Optional[float] = None


@dataclass
class IngestReport:
    file_id: str
    status: str
    message: str
    processed_at: datetime
    records_processed: int
    kpi_records_upserted: int
