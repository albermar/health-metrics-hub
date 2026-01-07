from __future__ import annotations

from datetime import datetime, timezone, time
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import DailyKPIsOutput, DailyMetricsInput
from app.domain.interfaces import OutputRepository_Interface, InputRepository_Interface
from app.infrastructure.db.models import DailyKPIORM, DailyInputORM


"""
Repository implementation (Infrastructure layer)

Key idea:
- This class knows about SQLAlchemy + Postgres + ORM models.
- It DOES NOT know about FastAPI routers or HTTP.
- It receives an already-created SQLAlchemy Session (dependency injection).
"""


class Postgres_OutputRepository(OutputRepository_Interface):
    """
    PostgreSQL implementation of OutputRepository_Interface.

    The router (API layer) is the "composition root":
        Router -> Build DB session -> Build Repo(session) -> Build Use Case(repo) -> Execute use case
    """
    
    def __init__(self, db_session: Session):
        self._db = db_session #Injected SQLAlchemy session

    def save_output(self, output_data: list[DailyKPIsOutput]) -> None:
        """
        Upsert KPI rows by day:
        - If day doesn't exist -> INSERT
        - If day exists -> UPDATE
        - Commit once at the end (batch commit)

        Why commit once?
        - Better performance (one transaction)
        - Easier rollback semantics ("all or nothing")
        """
        try:
            for kpi in output_data:
                # DB uses a date column as the business key ("one row per day")
                day_to_check = kpi.date.date()

                # 1) Check if a row for this day already exists
                stmt = select(DailyKPIORM).where(DailyKPIORM.day == day_to_check)
                existing_row = self._db.execute(stmt).scalar_one_or_none()

                if existing_row is None:
                    # 2a) INSERT: create a new ORM instance and add it to the session
                    new_row = DailyKPIORM(
                        day=day_to_check,

                        # Reduced KPI set (8)
                        kcal_out_total=kpi.kcal_out_total,
                        balance_kcal=kpi.balance_kcal,
                        balance_7d_average=kpi.balance_7d_average,
                        protein_per_kg=kpi.protein_per_kg,
                        healthy_food_pct=kpi.healthy_food_pct,
                        adherence_steps=kpi.adherence_steps,
                        weight_7d_avg=kpi.weight_7d_avg,
                        waist_change_7d=kpi.waist_change_7d,

                        # "when was this computed?"
                        computed_at=datetime.now(timezone.utc),
                    )
                    self._db.add(new_row)

                else:
                    # 2b) UPDATE: mutate the existing ORM instance
                    # (SQLAlchemy is tracking it already; no need to re-add)
                    existing_row.kcal_out_total = kpi.kcal_out_total
                    existing_row.balance_kcal = kpi.balance_kcal
                    existing_row.balance_7d_average = kpi.balance_7d_average
                    existing_row.protein_per_kg = kpi.protein_per_kg
                    existing_row.healthy_food_pct = kpi.healthy_food_pct
                    existing_row.adherence_steps = kpi.adherence_steps
                    existing_row.weight_7d_avg = kpi.weight_7d_avg
                    existing_row.waist_change_7d = kpi.waist_change_7d
                    existing_row.computed_at = datetime.now(timezone.utc)

            # 3) Persist everything at once
            self._db.commit()

        except Exception:
            # If anything fails, revert the entire transaction (no partial writes)
            self._db.rollback()
            raise

    def get_output(self, start: datetime, end: datetime) -> list[DailyKPIsOutput]:
        """
        Read KPI rows in the date range [start, end], ordered by day.

        Important notes:
        - This method is READ-ONLY, so we do NOT commit/rollback here.
        - Session lifecycle (close) is handled outside by FastAPI dependency injection.
        - We map ORM objects -> DOMAIN entities (DailyKPIsOutput).
        """
        # 1) Query ORM rows in range
        stmt = (
            select(DailyKPIORM)
            .where(DailyKPIORM.day >= start.date(), DailyKPIORM.day <= end.date())
            .order_by(DailyKPIORM.day.asc())
        )
        orm_rows = self._db.execute(stmt).scalars().all()
        # scalars(): return ORM objects directly (not full result tuples)
        # all(): fetch everything into a list (can be empty; that's fine)

        # 2) Map ORM -> Domain
        domain_entities: list[DailyKPIsOutput] = []

        for row in orm_rows:
            domain_entities.append(
                DailyKPIsOutput(
                    # ORM stores date (no time). Convert to a timezone-aware datetime.
                    date=datetime.combine(row.day, time.min, tzinfo=timezone.utc),

                    # Reduced KPI set (8)
                    kcal_out_total=row.kcal_out_total,
                    balance_kcal=row.balance_kcal,
                    balance_7d_average=row.balance_7d_average,
                    protein_per_kg=row.protein_per_kg,
                    healthy_food_pct=row.healthy_food_pct,
                    adherence_steps=row.adherence_steps,
                    weight_7d_avg=row.weight_7d_avg,
                    waist_change_7d=row.waist_change_7d,
                )
            )

        return domain_entities


class Postgres_InputRepository(InputRepository_Interface):
    def __init__(self, db_session: Session):
        self._db = db_session
    def save_input(self, input_data: list[DailyMetricsInput]) -> None :
        try:            
            for input_record in input_data:
                date_to_check = input_record.date.date()
                #check if a record for this date already exists
                stmt = select(DailyInputORM).where(DailyInputORM.date == date_to_check)
                existing_row = self._db.execute(stmt).scalar_one_or_none()
                
                if existing_row is None:
                    new_row = DailyInputORM(
                        date = date_to_check,
                        steps_n = input_record.steps_n,
                        proteins_g = input_record.proteins_g,
                        kcal_in = input_record.kcal_in,
                        kcal_junk_in = input_record.kcal_junk_in,
                        kcal_out_training = input_record.kcal_out_training,
                        sleep_hours = input_record.sleep_hours,
                        stress_rel = input_record.stress_rel,
                        weight_kg = input_record.weight_kg,
                        waist_cm = input_record.waist_cm
                    )
                    self._db.add(new_row)
                else:
                    existing_row.steps_n = input_record.steps_n
                    existing_row.proteins_g = input_record.proteins_g
                    existing_row.kcal_in = input_record.kcal_in
                    existing_row.kcal_junk_in = input_record.kcal_junk_in
                    existing_row.kcal_out_training = input_record.kcal_out_training
                    existing_row.sleep_hours = input_record.sleep_hours
                    existing_row.stress_rel = input_record.stress_rel
                    existing_row.weight_kg = input_record.weight_kg
                    existing_row.waist_cm = input_record.waist_cm                
                
            #after upserting all records, commit once
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
    def get_input(self, start: datetime, end: datetime) -> list[DailyMetricsInput]:
        """
        Read input rows in the date range [start, end], ordered by date.

        Notes:
        - READ-ONLY: no commit/rollback.
        - Session lifecycle is managed outside (FastAPI dependency).
        - Maps ORM rows -> domain entities (DailyMetricsInput).
        """
        if start > end:
            raise ValueError("Start date must be before end date.")

        # 1) Query ORM rows in range (inclusive)
        stmt = (
            select(DailyInputORM)
            .where(DailyInputORM.date >= start.date(), DailyInputORM.date <= end.date())
            .order_by(DailyInputORM.date.asc())
        )
        orm_rows = self._db.execute(stmt).scalars().all()

        # 2) Map ORM -> Domain
        domain_entities: list[DailyMetricsInput] = []

        for row in orm_rows:
            domain_entities.append(
                DailyMetricsInput(
                    # ORM stores a DATE. Convert to timezone-aware datetime at midnight UTC.
                    date=datetime.combine(row.date, time.min, tzinfo=timezone.utc),

                    steps_n=row.steps_n,
                    proteins_g=row.proteins_g,
                    kcal_in=row.kcal_in,
                    kcal_junk_in=row.kcal_junk_in,
                    kcal_out_training=row.kcal_out_training,
                    sleep_hours=row.sleep_hours,
                    stress_rel=row.stress_rel,
                    weight_kg=row.weight_kg,
                    waist_cm=row.waist_cm,
                )
            )

        return domain_entities
            
            