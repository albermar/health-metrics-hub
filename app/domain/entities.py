from datetime import datetime


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

class DailyKPIsOutput: 
    #Some KPI need older data to be calculated, so we mark them with _ prefix
    date: datetime
    # Energy Balance
    basal_spend: float
    neat_from_steps: float
    kcal_out_total: float
    balance_kcal: float
    balance_7d_average: float
    # Nutrition
    protein_per_kg: float
    protein_pct: float
    healthy_food_pct: float
    # Activity
    adherence_steps: int
    steps_7d_avg: float
    steps_slope: float
    # Physiology
    weight_7d_avg: float
    weight_slope: float
    kg_fat_loss: float
    waist_change_7d: float
    # Recovery
    sleep_7d_avg: float
    stress_7d_avg: float