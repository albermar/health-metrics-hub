from datetime import date, datetime, timezone

from app.business.kpi_calculator import compute_daily_kpis
from app.domain.entities import DailyMetricsInput


def test_compute_daily_kpis_returns_empty_list_when_no_records():
    result = compute_daily_kpis(
        records=[],
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
    )

    assert result == []


def test_compute_daily_kpis_single_day_basic_metrics():
    record = DailyMetricsInput(
        date=datetime(2026, 1, 10, tzinfo=timezone.utc),
        steps_n=10_000,
        proteins_g=120,
        kcal_in=2_500,
        kcal_junk_in=500,
        kcal_out_training=2_000,
        stress_rel=None,
        sleep_hours=None,
        weight_kg=80.0,
        waist_cm=None 
    )

    result = compute_daily_kpis(
        records=[record],
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
        target_steps=10_000,
    )

    assert len(result) == 1

    kpi = result[0]

    assert kpi.balance_kcal == 500.0  # 2500 - 2000
    assert round(kpi.protein_per_kg, 2) == 1.5  # 120 / 80
    assert round(kpi.healthy_food_pct, 1) == 80.0  # 1 - (500 / 2500)
    assert kpi.adherence_steps == 1
    
    
    
def test_compute_daily_kpis_balance_7d_average_day7_is_correct():        
    records = []
    for d in range(1, 8):  # Jan 1..Jan 7
        records.append(
            DailyMetricsInput(
                date=datetime(2026, 1, d, tzinfo=timezone.utc),
                steps_n=10_000,
                proteins_g=100,
                kcal_in=2_500,
                kcal_junk_in=0,
                kcal_out_training=2_000,  # balance = 500 each day
                stress_rel=None,
                sleep_hours=None,
                weight_kg=80.0,
                waist_cm=None,
            )
        )

    result = compute_daily_kpis(
        records=records,
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
        target_steps=10_000,
    )

    # Find KPI for Jan 7 (last one)
    kpi_day7 = result[-1]
    assert kpi_day7.balance_kcal == 500.0
    assert round(kpi_day7.balance_7d_average, 2) == 500.0


def test_compute_daily_kpis_weight_7d_avg_day7_is_correct():
    records = [
        DailyMetricsInput(
            date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=80.0,
            waist_cm=None,
        ),
        DailyMetricsInput(
            date=datetime(2026, 1, 2, tzinfo=timezone.utc),
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=81.0,
            waist_cm=None,
        ),
        DailyMetricsInput(
            date=datetime(2026, 1, 3, tzinfo=timezone.utc),
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=82.0,
            waist_cm=None,
        ),
        DailyMetricsInput(
            date=datetime(2026, 1, 4, tzinfo=timezone.utc),
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=83.0,
            waist_cm=None,
        ),
        DailyMetricsInput(
            date=datetime(2026, 1, 5, tzinfo=timezone.utc),
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=84.0,
            waist_cm=None,
        ),
        DailyMetricsInput(
            date=datetime(2026, 1, 6, tzinfo=timezone.utc),
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=85.0,
            waist_cm=None,
        ),
        DailyMetricsInput(
            date=datetime(2026, 1, 7, tzinfo=timezone.utc),
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=86.0,
            waist_cm=None,
        ),
    ]

    result = compute_daily_kpis(
        records=records,
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
        target_steps=10_000,
    )

    # We want the KPI for Jan 7
    kpi_day7 = result[-1]

    # Mean of weights [80..86] = 581 / 7 = 83.00
    assert round(kpi_day7.weight_7d_avg, 2) == 83.00



def test_compute_daily_kpis_respects_start_end_date_filter():
    records = [
        DailyMetricsInput(
            date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=80.0,
            waist_cm=None,
        ),
        DailyMetricsInput(
            date=datetime(2026, 1, 10, tzinfo=timezone.utc),
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=81.0,
            waist_cm=None,
        ),
        DailyMetricsInput(
            date=datetime(2026, 1, 20, tzinfo=timezone.utc),
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=82.0,
            waist_cm=None,
        ),
    ]

    result = compute_daily_kpis(
        records=records,
        start=date(2026, 1, 5),
        end=date(2026, 1, 15),
        target_steps=10_000,
    )

    assert len(result) == 1
    assert result[0].date == date(2026, 1, 10) or str(result[0].date).startswith("2026-01-10")



def test_compute_daily_kpis_handles_missing_values_safely():
    record = DailyMetricsInput(
        date=datetime(2026, 1, 10, tzinfo=timezone.utc),
        steps_n=None,
        proteins_g=None,
        kcal_in=None,
        kcal_junk_in=None,
        kcal_out_training=None,
        stress_rel=None,
        sleep_hours=None,
        weight_kg=None,
        waist_cm=None,
    )

    result = compute_daily_kpis(
        records=[record],
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
    )

    kpi = result[0]

    assert kpi.balance_kcal is None
    assert kpi.protein_per_kg is None
    assert kpi.healthy_food_pct is None
    assert kpi.adherence_steps is None
    assert kpi.weight_7d_avg is None



def test_compute_daily_kpis_weight_7d_avg_with_missing_days():
    records = [
        DailyMetricsInput(
            date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=80.0,
            waist_cm=None,
        ),
        DailyMetricsInput(
            date=datetime(2026, 1, 4, tzinfo=timezone.utc),  # gap
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=82.0,
            waist_cm=None,
        ),
        DailyMetricsInput(
            date=datetime(2026, 1, 7, tzinfo=timezone.utc),
            steps_n=10_000,
            proteins_g=100,
            kcal_in=2000,
            kcal_junk_in=0,
            kcal_out_training=2000,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=86.0,
            waist_cm=None,
        ),
    ]

    result = compute_daily_kpis(
        records=records,
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
    )

    kpi_day7 = result[-1]

    # average of available weights only: (80 + 82 + 86) / 3 = 82.67
    assert round(kpi_day7.weight_7d_avg, 2) == 82.67


def test_compute_daily_kpis_waist_change_7d():
    records = [
        DailyMetricsInput(
            date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            steps_n=None,
            proteins_g=None,
            kcal_in=None,
            kcal_junk_in=None,
            kcal_out_training=None,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=None,
            waist_cm=90.0,
        ),
        DailyMetricsInput(
            date=datetime(2026, 1, 8, tzinfo=timezone.utc),
            steps_n=None,
            proteins_g=None,
            kcal_in=None,
            kcal_junk_in=None,
            kcal_out_training=None,
            stress_rel=None,
            sleep_hours=None,
            weight_kg=None,
            waist_cm=88.0,
        ),
    ]

    result = compute_daily_kpis(
        records=records,
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
    )

    kpi_day8 = result[-1]

    assert kpi_day8.waist_change_7d == -2.0
