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
from datetime import datetime
from app.domain.interfaces import OutputRepository_Interface
from app.domain.entities import DailyKPIsOutput


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