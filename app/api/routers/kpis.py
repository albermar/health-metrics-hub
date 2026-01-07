from fastapi import APIRouter, Query
from datetime import datetime
from app.api.schemas import DailyKPIsResponse
from fastapi import HTTPException
from app.infrastructure.db.repository_impl import Postgres_OutputRepository
from app.infrastructure.db.engine import get_db_session

from sqlalchemy.orm import Session

from fastapi import Depends

from app.business.use_cases import GetKPIs




router = APIRouter()

#Get endpoint to retrieve KPIs for a given date range

@router.get("/kpis/", response_model = list[DailyKPIsResponse])
def get_kpis(
    start_date: datetime = Query(..., description = "Start date in YYYY-MM-DD format"),
    end_date:   datetime = Query(..., description = "End date in YYYY-MM-DD format"), 
    db: Session = Depends(get_db_session) # this is the injected SQLAlchemy Session
    ):
    
    #1 ) Build repository (DI)
    repo = Postgres_OutputRepository(db_session = db)
    
    #2) Build use case
    use_case = GetKPIs(output_repo = repo)
    
    #3) Execute use case    
    try:
        domain_rows = use_case.execute(start = start_date, end = end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
    #4) Build Pydantic response. Map DOMAIN -> API schema (DTO) to return JSON
    response = [DailyKPIsResponse.from_domain(domain_obj) for domain_obj in domain_rows]
    
    return response