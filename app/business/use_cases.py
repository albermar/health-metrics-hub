#Let's build our first use case
# Given start and end dates, return the KPIs in that range.
# To do that, the use case needs to call the repository port
"""
Use case: Get KPIs for a date range.

WHY THIS FILE EXISTS:
- FastAPI routes should NOT talk directly to SQLAlchemy or Postgres repositories.
- Routes should delegate to a "use case" that orchestrates the operation.
- This makes the operation reusable (CLI, tests, background jobs) and keeps boundaries clean.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from app.api.routers import kpis
from app.business.kpi_calculator import compute_daily_kpis
from app.domain.entities import DailyKPIsOutput, DailyMetricsInput, IngestReport, DailyMetricsInput

from app.domain.interfaces import (
    OutputRepository_Interface,
    InputRepository_Interface,
    FileStorage_Interface,
    CSVParser_Interface,
)
@dataclass(frozen=True) 
class GetKPIs:
    
    output_repo: OutputRepository_Interface
    
    def execute(self, start: datetime, end: datetime) -> list[DailyKPIsOutput]:
        if start > end:
            raise ValueError("Start date must be before end date.")
        
        return self.output_repo.get_output(start, end)
"""
========================
LEARNING NOTES (FOR ME)
========================

WHAT THIS USE CASE DOES
- Represents one business operation: "get KPIs for a date range".
- It does NOT know anything about FastAPI, SQLAlchemy, Postgres, or HTTP.
- It only orchestrates the operation using a repository port.

WHY THIS CLASS EXISTS
- FastAPI routes should not contain business logic.
- Routes delegate to use cases so the logic can be reused
  (API, CLI, background jobs, tests).
- This is the "application layer" in Clean Architecture.

WHY @dataclass
- This object only stores dependencies + exposes execute().
- dataclass auto-generates __init__, reducing boilerplate.
- Dependencies are explicit and visible in the class signature.

WHY frozen=True
- Makes the use case immutable after creation.
- Prevents accidental reassignment of the repository.
- Makes behavior easier to reason about.

WHY output_repo IS AN INTERFACE
- The use case depends on an abstraction (port), not an implementation.
- The real repository (Postgres_OutputRepository) is injected
  from the API layer (composition root).
- This allows swapping implementations without touching the use case.

WHAT HAPPENS AT RUNTIME
- FastAPI route creates a Postgres_OutputRepository(db_session).
- That concrete object is passed into GetKPIs(output_repo=...).
- execute() calls get_output() on the *actual* repository instance.
- Python resolves the method dynamically (polymorphism).

WHY WE VALIDATE start <= end HERE
- This is a business rule, not an HTTP concern.
- Even if FastAPI validates inputs, the rule must live in the use case.
- The API layer translates ValueError into HTTP 400.

WHY THE RETURN TYPE IS list[DailyKPIsOutput]
- Use cases speak in terms of DOMAIN entities.
- They do NOT return ORM models.
- They do NOT return Pydantic schemas.
- Mapping to API schemas happens in the API layer.

KEY CLEAN ARCHITECTURE RULE APPLIED
- High-level policy (use case) depends on abstractions.
- Low-level details (Postgres, SQLAlchemy) depend on the same abstractions.
- Dependency direction always points inward.
"""

@dataclass(frozen=True)
class IngestDailyCSV:
    input_repo: InputRepository_Interface
    output_repo: OutputRepository_Interface
    file_storage: FileStorage_Interface
    parser: CSVParser_Interface
    
    def execute(self, file_bytes: bytes, filename: str) -> IngestReport:
        """
        Ingest a daily metrics CSV file:
        - Save the uploaded file using the file storage port.
        - Parse the CSV and create DailyMetricsInput entities.
        - Save inputs using the input repository port.
        - Compute KPIs and save them using the output repository port.
        - Move the file to processed or unprocessable based on success/failure of all steps.
        - Return an IngestReport entity summarizing the operation.
        """
        processed_at = datetime.now(timezone.utc) 
        safe_filename = filename or "upload.csv"
        
        file_id: str | None = None 
        records: list[DailyMetricsInput] = []
        kpis: list[DailyKPIsOutput] = []
        
        try:
            # 1. Save raw file
            file_id = self.file_storage.save_uploaded_csv(file_bytes=file_bytes, filename=safe_filename)
            
            # 2. Parse CSV
            records = self.parser.parse(file_bytes=file_bytes)
            
            # 3. Save inputs
            self.input_repo.save_input(input_data=records)
            
            # 4) Compute KPI range from uploaded records
            upload_start = min(r.date.date() for r in records)
            upload_end = max(r.date.date() for r in records)

            # Fetch context (previous 6 days) for rolling windows
            context_start = upload_start - timedelta(days=6)
            context_records = self.input_repo.get_input(start=context_start, end=upload_end)

            # Compute KPIs only for upload range, using context for rolling stats
            kpis = compute_daily_kpis(context_records, start=upload_start, end=upload_end, target_steps=10000)
            
            # 5. Save outputs
            if kpis:
                self.output_repo.save_output(output_data=kpis)         

            # 6. Move file to processed
            self.file_storage.move_csv_to_processed(file_id=file_id)
            
            return IngestReport(
                file_id=file_id,
                status="processed",
                message="CSV ingested successfully.",
                processed_at=processed_at,
                records_processed=len(records),
                kpi_records_upserted=len(kpis),
            )
            
        except Exception as e:
            # Best effort: mark file as unprocessable if we managed to save it
            if file_id is not None:
                try:
                    self.file_storage.move_csv_to_unprocessable(file_id)
                except Exception:
                    # don't hide the original error
                    pass

            return IngestReport(
                file_id=file_id or "",
                status="unprocessable",
                message=str(e),
                processed_at=processed_at,
                records_processed=len(records),
                kpi_records_upserted=len(kpis),
            )
       
            
  