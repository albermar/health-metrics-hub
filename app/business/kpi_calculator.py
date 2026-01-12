
from __future__ import annotations

from datetime import datetime, date, time, timezone, timedelta
from typing import Optional

from app.domain.entities import DailyMetricsInput, DailyKPIsOutput


def compute_daily_kpis(
    records: list[DailyMetricsInput],
    *,
    start: date,
    end: date,
    target_steps: int = 10_000,
) -> list[DailyKPIsOutput]:
    
    if not records:
        return []

    # 1) Create a dictionaty with day, inputs. We will add the inputs by day, and sort later. If a day is duplicated, because of the dictionaries nature (no repeated keys), the last one will remain.
    dict_inputs: dict[date, DailyMetricsInput] = {}
    
    for r in records:
        #we are creating a key, value pair where the key is the date object representing the day of the record r, and the value is the DailyMetricsInput object for that day.
        dict_inputs[r.date.date()] = r 
    
    # 2) Sort days with sorted()
    days_sorted: list[date] = sorted(dict_inputs.keys())

    # Rolling helpers (store computed daily values so rolling windows can look back)
    balance_by_day: dict[date, Optional[float]] = {}
    weight_by_day: dict[date, Optional[float]] = {}
    waist_by_day: dict[date, Optional[float]] = {}

    results: list[DailyKPIsOutput] = []

    for d in days_sorted: #we are iterating over the sorted list of dates, and for each date d, we are getting the corresponding DailyMetricsInput object r from the dict_inputs dictionary.
        #r is a DailyMetricsInput object for that day, but we are iterating over unique days + sorted.
        r = dict_inputs[d]

        # ---- Per-day KPIs ----
        
        kcal_out_total: Optional[float] = None
        if r.kcal_out_training is not None:
            kcal_out_total = float(r.kcal_out_training)

        balance_kcal: Optional[float] = None
        if r.kcal_in is not None and kcal_out_total is not None:
            balance_kcal = float(r.kcal_in) - kcal_out_total

        protein_per_kg: Optional[float] = None
        if r.proteins_g is not None and r.weight_kg is not None and r.weight_kg > 0:
            protein_per_kg = float(r.proteins_g) / float(r.weight_kg)

        healthy_food_pct: Optional[float] = None
        if r.kcal_in is not None and r.kcal_in > 0 and r.kcal_junk_in is not None:
            healthy_food_pct = 100.0 * (1.0 - (float(r.kcal_junk_in) / float(r.kcal_in)))

        adherence_steps: Optional[int] = None
        if r.steps_n is not None:
            adherence_steps = 1 if r.steps_n >= target_steps else 0

        # Store daily values for rolling computations (even if outside target range)
        # this are dictionaries where the key is the date and the value is the computed metric for that day. 
        # we will use these dictionaries later to compute rolling averages and changes over a 7-day window.
        balance_by_day[d] = balance_kcal
        weight_by_day[d] = float(r.weight_kg) if r.weight_kg is not None else None
        waist_by_day[d] = float(r.waist_cm) if r.waist_cm is not None else None

        # Only output KPIs for target range
        # if the current day d is outside the specified start and end dates, we skip the rest of the loop and move to the next day.
        # but we have already stored the daily values for rolling computations above.
        if d < start or d > end:
            continue
        
        # now here we are inside the target range, and we will compute the rolling 7-day KPIs.
        
        # Rolling 7d KPIs (current day + previous 6 days)
        #this creates a list of dates representing the current day d and the previous 6 days.
        window_days = [d - timedelta(days=i) for i in range(0, 7)]
        #example: if d is 2024-06-10, window_days will be [2024-06-10, 2024-06-09, 2024-06-08, 2024-06-07, 2024-06-06, 2024-06-05, 2024-06-04]
        
        balances = [balance_by_day.get(x) for x in window_days]
        # example: [None, -200.0, 150.0, None, 0.0, 100.0, -50.0]
        balances = [v for v in balances if v is not None]
        # example: [-200.0, 150.0, 0.0, 100.0, -50.0]
        balance_7d_average = (sum(balances) / len(balances)) if balances else None
        # example: (-200 + 150 + 0 + 100 - 50) / 5 = 0.0
        
        #the same
        weights = [weight_by_day.get(x) for x in window_days]
        weights = [v for v in weights if v is not None]
        weight_7d_avg = (sum(weights) / len(weights)) if weights else None

        waist_change_7d: Optional[float] = None
        waist_today = waist_by_day.get(d)        
        waist_7ago = waist_by_day.get(d - timedelta(days=7))
        
        if waist_today is not None and waist_7ago is not None:
            waist_change_7d = waist_today - waist_7ago

        results.append(
            DailyKPIsOutput(
                date=datetime.combine(d, time.min, tzinfo=timezone.utc),
                kcal_out_total=kcal_out_total,
                balance_kcal=balance_kcal,
                balance_7d_average=balance_7d_average,
                protein_per_kg=protein_per_kg,
                healthy_food_pct=healthy_food_pct,
                adherence_steps=adherence_steps,
                weight_7d_avg=weight_7d_avg,
                waist_change_7d=waist_change_7d,
            )
        )

    return results