from fastapi import APIRouter, UploadFile, File
from app.infrastructure.db.engine import get_db_session
from sqlalchemy.orm import Session
from fastapi import Depends
from app.infrastructure.db.models import DailyKPIORM, DailyInputORM
from app.infrastructure.db.repository_impl import DI_Postgres_InputRepository, DI_Postgres_OutputRepository
from app.infrastructure.parser.parser_impls import DI_CsvParserV1

from app.infrastructure.storage.storage_impl import DI_LocalFileStorage

from app.business.use_cases import IngestDailyCSV
from app.api.schemas import IngestReportResponse


router = APIRouter()

'''
TODO:
- Implement execute() method in IngestDailyCSV use case
- Implement save_input() and get_input() methods in Postgres_InputRepository

'''

@router.post("/upload-csv", response_model=IngestReportResponse)
async def upload_daily_csv(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    
    '''
    # ⚠️ DEV ONLY: wipe all previous KPIs
    db.query(DailyKPIORM).delete()
    db.query(DailyInputORM).delete()
    db.commit()
    '''
    
    
    #Process the UploadFile (Extract bytes and filename)
    file_bytes = await file.read() 
    filename = file.filename or "upload.csv"
    
    #create the 2 repositories (DI)
    input_repo = DI_Postgres_InputRepository(db_session = db)
    output_repo = DI_Postgres_OutputRepository(db_session = db)
    
    #create the implementation for the file storage intarface (DI) 
    file_storage = DI_LocalFileStorage(base_path="./storage")
    
    #create the parser implementation
    parser = DI_CsvParserV1()
    
    #Build the use case:
    use_case = IngestDailyCSV(input_repo = input_repo, 
                              output_repo = output_repo, 
                              file_storage = file_storage, 
                              parser = parser)
    
    #Execute the use case
    report = use_case.execute(file_bytes = file_bytes, filename = filename)
    
    #Build the response mapping DOMAIN -> API schema (DTO)
    report_response = IngestReportResponse.from_domain(report)
    
    #Return the response (Pydantic model)
    return report_response


