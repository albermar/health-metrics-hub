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
from datetime import date, datetime, time, timedelta
from typing import Optional
from app.domain.interfaces import OutputRepository_Interface
from app.domain.entities import DailyKPIsOutput, DailyMetricsInput, IngestReport, DailyMetricsInput

from app.domain.interfaces import OutputRepository_Interface, InputRepository_Interface, InputFileStorage_Interface, CSVParser_Interface

N_DAYS = 7
LOOKBACK = N_DAYS - 1
STEP_GOAL = 8000


def compute_kpi_recompute_range(uploaded: list[DailyMetricsInput]) -> tuple[date, date]:
    """
    Trailing-window rule:
    - inputs on day X affect KPI rows for X..X+LOOKBACK
    """
    days = [x.date.date() for x in uploaded]
    start = min(days)
    end = max(days) + timedelta(days=LOOKBACK)
    return start, end


def compute_required_input_range(kpi_start: date, kpi_end: date) -> tuple[date, date]:
    """
    To compute KPI(day D) we need inputs from D-LOOKBACK..D.
    Therefore for KPI range [kpi_start..kpi_end], need inputs:
      [kpi_start-LOOKBACK .. kpi_end]
    """
    return kpi_start - timedelta(days=LOOKBACK), kpi_end


def _as_midnight(d: date) -> datetime:
    return datetime.combine(d, time.min)


def _clamp_0_1(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def estimate_neat_kcal_from_steps(steps_n: int, weight_kg: float) -> Optional[float]:
    if steps_n is None or steps_n < 0:
        return None
    if weight_kg is None or weight_kg <= 0:
        return None

    base_kcal_per_step = 0.05
    weight_factor = float(weight_kg) / 80.0
    return float(steps_n) * base_kcal_per_step * weight_factor




def compute_kpis_for_range(
    inputs: list[DailyMetricsInput],
    kpi_start: date,
    kpi_end: date,
) -> list[DailyKPIsOutput]:
    """
    Pure KPI computation:
    - no repo calls
    - expects all needed inputs already fetched
    - returns one KPI row per day (only for days that exist in inputs)
    """

    by_day: dict[date, DailyMetricsInput] = {i.date.date(): i for i in inputs}

    def get_input(d: date) -> Optional[DailyMetricsInput]:
        return by_day.get(d)

    def kcal_out_total(inp: DailyMetricsInput) -> Optional[float]:
        neat = estimate_neat_kcal_from_steps(inp.steps_n, inp.weight_kg)
        # If NEAT can't be computed, still count training kcal
        return float(inp.kcal_out_training) if neat is None else float(inp.kcal_out_training) + neat

    def balance_kcal(inp: DailyMetricsInput) -> Optional[float]:
        out_total = kcal_out_total(inp)
        if out_total is None:
            return None
        return float(inp.kcal_in) - out_total

    def protein_per_kg(inp: DailyMetricsInput) -> Optional[float]:
        if inp.weight_kg is None or inp.weight_kg <= 0:
            return None
        return float(inp.proteins_g) / float(inp.weight_kg)

    def healthy_food_pct(inp: DailyMetricsInput) -> Optional[float]:
        if inp.kcal_in is None or inp.kcal_in <= 0:
            return None
        pct = 1.0 - (float(inp.kcal_junk_in) / float(inp.kcal_in))
        return _clamp_0_1(pct)

    def adherence_steps(inp: DailyMetricsInput) -> Optional[int]:
        if inp.steps_n is None:
            return None
        return 1 if inp.steps_n >= STEP_GOAL else 0

    def rolling_days(end_day: date) -> list[date]:
        return [end_day - timedelta(days=offset) for offset in range(LOOKBACK, -1, -1)]

    def balance_7d_average(d: date) -> Optional[float]:
        vals: list[float] = []
        for day in rolling_days(d):
            inp = get_input(day)
            if inp is None:
                return None
            b = balance_kcal(inp)
            if b is None:
                return None
            vals.append(b)
        return sum(vals) / float(N_DAYS)

    def weight_7d_avg(d: date) -> Optional[float]:
        vals: list[float] = []
        for day in rolling_days(d):
            inp = get_input(day)
            if inp is None or inp.weight_kg is None:
                return None
            vals.append(float(inp.weight_kg))
        return sum(vals) / float(N_DAYS)

    def waist_change_7d(d: date) -> Optional[float]:
        today = get_input(d)
        prev = get_input(d - timedelta(days=7))
        if today is None or prev is None:
            return None
        if today.waist_cm is None or prev.waist_cm is None:
            return None
        return float(today.waist_cm) - float(prev.waist_cm)

    results: list[DailyKPIsOutput] = []
    d = kpi_start
    while d <= kpi_end:
        inp = get_input(d)
        if inp is not None:
            results.append(
                DailyKPIsOutput(
                    date=_as_midnight(d),
                    kcal_out_total=kcal_out_total(inp),
                    balance_kcal=balance_kcal(inp),
                    balance_7d_average=balance_7d_average(d),
                    protein_per_kg=protein_per_kg(inp),
                    healthy_food_pct=healthy_food_pct(inp),
                    adherence_steps=adherence_steps(inp),
                    weight_7d_avg=weight_7d_avg(d),
                    waist_change_7d=waist_change_7d(d),
                )
            )
        d += timedelta(days=1)

    return results


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
    file_storage: InputFileStorage_Interface
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
        # Save the uploaded CSV file and get a file_id
        file_id = self.file_storage.save_uploaded_csv(file_bytes = file_bytes, filename = filename)
        
        try:
            # Parse the CSV file into DailyMetricsInput entities
            # (Parsing logic not shown here; assume we get input_data as a list)
            input_data: list[DailyMetricsInput] = self.parser.parse_csv(file_bytes = file_bytes)
            if not input_data:
                raise ValueError("No valid input data found in CSV.")
            
            # Upsert input data using the input repository
            self.input_repo.save_input(input_data = input_data)
            
            # Determine KPI recompute range based on input_data dates
            kpi_start, kpi_end = compute_kpi_recompute_range(input_data)
            
            # Determine required input range for KPI computation
            input_needed_start, input_needed_end = compute_required_input_range(kpi_start, kpi_end)
            
            window_inputs = self.input_repo.get_input(start = input_needed_start, end = input_needed_end)
            
            # Compute KPIs for the given date range and the loaded inputs
            computed_kpis = compute_kpis_for_range(window_inputs, kpi_start, kpi_end)            
            # Save the KPI output data using the output repository
            self.output_repo.save_output(output_data = computed_kpis  )
            
            # Mark file processed
            self.file_storage.move_csv_to_processed(file_id = file_id)
            
            #7) 
            return IngestReport(
                file_id=file_id,
                status="processed",
                message="File ingested successfully.",
                processed_at=datetime.utcnow(),
                records_processed=len(input_data),
                kpi_records_upserted=len(computed_kpis),
            )
        
        except Exception as e:
            #On any error, move the file to unprocessable
            self.file_storage.move_csv_to_unprocessable(file_id = file_id)
            
            #Build and return a failure IngestReport
            report = IngestReport(
                file_id = file_id,
                status = "unprocessable",
                message = f"Ingestion failed: {str(e)}",
                processed_at = datetime.utcnow(),
                records_processed = 0,
                kpi_records_upserted = 0
            )
            return report
  