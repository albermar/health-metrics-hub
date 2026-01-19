#ORM models (tables)
'''
models.py is infrastructure-only. Defines how data is stored in postgres
- tables (ORM classes)
- columns + types
- constraints (primary key, unique, not null)
'''

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import Date, Integer, Float, String, UniqueConstraint
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime

from app.infrastructure.db.base import Base

#nullable=True means that the column can be left empty (NULL) in the DB



class DailyKPIORM(Base):
    __tablename__ = "daily_kpis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Energy / core
    kcal_out_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    balance_kcal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    balance_7d_average: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Nutrition
    protein_per_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    healthy_food_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Activity
    adherence_steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Physiology / trend
    weight_7d_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    waist_change_7d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("date", name="uq_daily_kpis_date"),
    )   


class DailyInputORM(Base):
    
    __tablename__ = "daily_inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    steps_n: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    proteins_g: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    kcal_in: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    kcal_junk_in: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    kcal_out_training: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
        
    stress_rel: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sleep_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint("date", name="uq_daily_inputs_date"),
    )
