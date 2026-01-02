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
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class DailyInputORM(Base):
    """
    Persistence model for raw daily metrics.

    This is NOT your domain entity.
    It's a database mapping (Infrastructure layer).
    """

    __tablename__ = "daily_inputs"

    # Primary key (internal DB identity)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Business key: one row per day (we enforce uniqueness)
    day: Mapped[date] = mapped_column(Date, nullable=False)

    # Example metrics (nullable=True because CSV may have missing values)
    steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    calories_in: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    calories_out: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sleep_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Optional body measurements (example)
    waist_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    chest_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    abdomen_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Optional notes / source tracking
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint("day", name="uq_daily_inputs_day"),
    )
