from datetime import datetime
from dataclasses import dataclass
from typing import Optional # for type hinting. Optional indicates that a field can be of a certain type or None.

@dataclass
class DailyMetricsInput:
    date: datetime
    steps_n: int
    proteins_g: int
    kcal_in: int
    kcal_junk_in: int
    kcal_out_training: int
    sleep_hours: float
    stress_rel: int #1-10 scale
    weight_kg: float
    waist_cm: float


'''
keep in mind that a domain entity has to:
1. store values
2. be easily created from various sources (e.g., DB records, API inputs)
3. be independent of frameworks (e.g., Pydantic, Django models)

that's the reason why we use decorator @dataclass, it creates init, repr, eq methods automatically
'''
@dataclass
class DailyKPIsOutput:
    date: datetime

    # Energy Balance
    basal_spend:        Optional[float] = None #Optional because in DB they have attribute nulable=True
    neat_from_steps:    Optional[float] = None
    kcal_out_total:     Optional[float] = None
    balance_kcal:       Optional[float] = None
    balance_7d_average: Optional[float] = None

    # Nutrition
    protein_per_kg:     Optional[float] = None
    protein_pct:        Optional[float] = None
    healthy_food_pct:   Optional[float] = None

    # Activity
    adherence_steps:    Optional[int] = None
    steps_7d_avg:       Optional[float] = None
    steps_slope:        Optional[float] = None

    # Physiology
    weight_7d_avg:      Optional[float] = None
    weight_slope:       Optional[float] = None
    kg_fat_loss:        Optional[float] = None
    waist_change_7d:    Optional[float] = None

    # Recovery
    sleep_7d_avg:       Optional[float] = None
    stress_7d_avg:      Optional[float] = None
