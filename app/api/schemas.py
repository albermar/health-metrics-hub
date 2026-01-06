from pydantic import BaseModel
from datetime import datetime

from app.domain.entities import DailyKPIsOutput


class DailyKPIsResponse(BaseModel):
    
    date: datetime

    # Energy / core
    kcal_out_total: float | None = None
    balance_kcal: float | None = None
    balance_7d_average: float | None = None

    # Nutrition
    protein_per_kg: float | None = None
    healthy_food_pct: float | None = None

    # Activity
    adherence_steps: int | None = None

    # Physiology / trend
    weight_7d_avg: float | None = None
    waist_change_7d: float | None = None

    @classmethod
    def from_domain(cls, domain_obj: DailyKPIsOutput) -> "DailyKPIsResponse":
        return cls(
            date=domain_obj.date,
            kcal_out_total=domain_obj.kcal_out_total,
            balance_kcal=domain_obj.balance_kcal,
            balance_7d_average=domain_obj.balance_7d_average,
            protein_per_kg=domain_obj.protein_per_kg,
            healthy_food_pct=domain_obj.healthy_food_pct,
            adherence_steps=domain_obj.adherence_steps,
            weight_7d_avg=domain_obj.weight_7d_avg,
            waist_change_7d=domain_obj.waist_change_7d,
        )
    
    
class IngestReportResponse(BaseModel):
    file_id: str
    status: str
    message: str
    processed_at: datetime
    records_processed: int
    kpi_records_upserted: int    
    @classmethod
    def from_domain(cls, domain_obj: "IngestReport") -> "IngestReportResponse":
        return cls(
            file_id=domain_obj.file_id,
            status=domain_obj.status,
            message=domain_obj.message,
            processed_at=domain_obj.processed_at,
            records_processed=domain_obj.records_processed,
            records_failed=domain_obj.records_failed,
        )
    