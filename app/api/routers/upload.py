from fastapi import APIRouter, UploadFile
from app.api.routers import kpis
from app.infrastructure.db.engine import get_db_session
from sqlalchemy.orm import Session
from fastapi import Depends
from app.infrastructure.db.repository_implementations import Postgres_InputRepository, Postgres_OutputRepository
from app.infrastructure.storage import LocalFileStorage

from app.business.use_cases import IngestDailyCSV

router = APIRouter()

'''
TODO:
- Implement execute() method in IngestDailyCSV use case
- Implement save_input() and get_input() methods in Postgres_InputRepository

'''

@router.post('/upload-csv', response_model = IngestReportResponse)
async def upload_daily_csv(file: UploadFile, db: Session = Depends(get_db_session)):
    #Process the UploadFile (Extract bytes and filename)
    file_bytes = await file.read()
    filename = file.filename
    
    #create the 2 repositories (DI)
    input_repo = Postgres_InputRepository(db_session = db)
    output_repo = Postgres_OutputRepository(db_session = db)
    
    #create the implementation for the file storage intarface (DI) 
    file_storage = LocalFileStorage(base_path="...")
    
    #create the parser
    parser = CsvParserV1()
    
    #Build the use case:
    use_case = IngestDailyCSV(input_repo = input_repo, 
                              output_repo = output_repo,
                              file_storage = file_storage, 
                              parser = parser)
    
    report = use_case.execute(file_bytes = file_bytes, filename = filename)
    
    return report


