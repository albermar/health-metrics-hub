from fastapi import APIRouter, Query
from datetime import datetime
from app.api.schemas import DailyKPIsResponse
from fastapi import HTTPException
from app.infrastructure.db.repository_impl import DI_Postgres_OutputRepository
from app.infrastructure.db.engine import get_db_session

from sqlalchemy.orm import Session

from fastapi import Depends

from app.business.use_cases import GetKPIs




router = APIRouter()

# Dependency provider for the repo. This function will be called by FastAPI to get an instance of the repository for each request. It uses the get_db_session dependency to get a database session and then creates an instance of DI_Postgres_OutputRepository with that session.
def get_output_repo(db: Session = Depends(get_db_session)) -> DI_Postgres_OutputRepository:
    return DI_Postgres_OutputRepository(db_session=db)



#Get endpoint to retrieve KPIs for a given date range
'''
Keep in mind that, if this endpoint is called is beacause the client wants to fetch kpis, so it's obvious that we'll need to query those kpis from a repo, so we anticipated it and passed the outputRepo as a parameter and we laid the groundwork
'''
@router.get("/kpis/", response_model = list[DailyKPIsResponse])
def get_kpis(
    start_date: datetime = Query(..., description = "Start date in YYYY-MM-DD format"),
    end_date:   datetime = Query(..., description = "End date in YYYY-MM-DD format"), 
    repo: DI_Postgres_OutputRepository = Depends(get_output_repo),
    ):
    
    #1 ) Build repository (DI)
    # OBSOLETE: repo = DI_Postgres_OutputRepository(db_session = db)
    
    #2) Build use case. The use case has different categories of elements, a repo to read, a start date, end date, etc. We can pass those parameters in the constructor or in the execute method, depending on how we want to design it. In this case, we pass the repo in the constructor and the dates in the execute method, but we could also pass everything in the execute method if we wanted to.
    use_case = GetKPIs(output_repo = repo)
    
    #3) Execute use case    
    try:
        domain_rows = use_case.execute(start = start_date, end = end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
    #4) Build Pydantic response. Map DOMAIN -> API schema (DTO) to return JSON
    response = [DailyKPIsResponse.from_domain(domain_obj) for domain_obj in domain_rows]
    
    return response