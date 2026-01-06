from __future__ import annotations

from datetime import datetime, timezone, time
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import DailyKPIsOutput
from app.domain.interfaces import OutputRepository_Interface
from app.infrastructure.db.models import DailyKPIORM


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
        # We assume the session lifecycle is managed outside (FastAPI Depends generator).
        self._db = db_session

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
