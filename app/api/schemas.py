from pydantic import BaseModel
from datetime import datetime


class DailyKPIsResponse(BaseModel):
    date: datetime
    # Energy Balance
    basal_spend: float
    neat_from_steps: float
    kcal_out_total: float
    balance_kcal: float
    _balance_7d_average: float
    # Nutrition
    protein_per_kg: float
    protein_pct: float
    healthy_food_pct: float
    # Activity
    adherence_steps: int
    _steps_7d_avg: float
    _steps_slope: float
    # Physiology
    _weight_7d_avg: float
    _weight_slope: float
    kg_fat_loss: float
    _waist_change_7d: float
    # Recovery
    _sleep_7d_avg: float
    _stress_7d_avg: float
        

    
    '''
    
    
class DailyKPIsOutput: 
    #Some KPI need older data to be calculated, so we mark them with _ prefix
    date: datetime
    # Energy Balance
    basal_spend: float
    neat_from_steps: float
    kcal_out_total: float
    balance_kcal: float
    _balance_7d_average: float
    # Nutrition
    protein_per_kg: float
    protein_pct: float
    healthy_food_pct: float
    # Activity
    adherence_steps: int
    _steps_7d_avg: float
    _steps_slope: float
    # Physiology
    _weight_7d_avg: float
    _weight_slope: float
    kg_fat_loss: float
    _waist_change_7d: float
    # Recovery
    _sleep_7d_avg: float
    _stress_7d_avg: float
    '''