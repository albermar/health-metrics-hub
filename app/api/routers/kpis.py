from fastapi import APIRouter, Query
from datetime import datetime
from app.api.schemas import DailyKPIsResponse
from fastapi import HTTPException
from app.infrastructure.repository_implementations import Postgres_OutputRepository

router = APIRouter()

#Get endpoint to retrieve KPIs for a given date range

@router.get("/kpis/", response_model = list[DailyKPIsResponse])
async def get_kpis(
    start_date: datetime = Query(..., description = "Start date in YYYY-MM-DD format"),
    end_date: datetime = Query(..., description = "End date in YYYY-MM-DD format")
    ):
    """
    Retrieve KPIs for the specified date range.
    1 ) Receive input (and validate it)
    2 ) Build Repository
    3 ) Build Use case
    4 ) Execute Use case     
    3 ) return the result as pydantic model
    
    No business logic
    No file I/O
    No DB logic
    No date validation logic
    No fetching logic
    """      
    #Receive and validate input. Because both are datetime, FastAPI will validate format automatically. If we had for example 2 strings, we would need to validate the format here and return HTTP 400 if invalid. But due to the use of datetime, FastAPI does it for us. Another 
    # Validation: 
    if (start_date > end_date):        
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")
    # 1. Input is valid at this point
    
    #Build the Repository (infrastructure implementation). But the repo needs a DB connection, which we are not handling here for simplicity. In a real app, we would use Dependency Injection to provide the repo with a DB session/connection
    # Create a DB session: 
    
    repo_kpis = Postgres_OutputRepository()
    
    #Build the use case and inject the repo
    
'''
    // 2. Build the repository (infrastructure implementation)
    repo = create instance of OutputRepository (file-based or DB-based)
    
    // 3. Build the use case and inject the repo
    use_case = new GetKPIsUseCase(repo)

    // 4. Execute the use case with the date range
    kpis = use_case.execute(start_date, end_date)

    // 5. Return the KPIs as JSON (DTO list)
    return kpis
    
'''