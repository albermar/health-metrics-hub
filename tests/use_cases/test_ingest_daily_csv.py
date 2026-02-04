#we will fake all external dependencies 
# parser
# input repo
# output repo
# storate adapter
# kpi calculator

#WE are going to fake the use case. RRemember the fastapi code:

'''
@router.post("/upload-csv", response_model=IngestReportResponse)
async def upload_daily_csv(file: UploadFile = File(...), db: Session = Depends(get_db_session)):   
    
            #Process the UploadFile (Extract bytes and filename)
            file_bytes = await file.read() 
            filename = file.filename or "upload.csv"
            
            #create the 2 repositories (DI)
FAKE-->     input_repo = DI_Postgres_InputRepository(db_session = db)
FAKE-->     output_repo = DI_Postgres_OutputRepository(db_session = db)
            
            #create the implementation for the file storage intarface (DI) 
FAKE-->     file_storage = DI_LocalFileStorage(base_path="./storage")
            
            #create the parser implementation
FAKE-->     parser = DI_CsvParserV1()
            
            #Build the use case:
            profile_path = Path("app/config/user_profile.json")
            profile = json.loads(profile_path.read_text(encoding="utf-8"))    
            steps_goal = int(profile.get("steps_goal", 10_000))
            
TEST-->     use_case = IngestDailyCSV(input_repo = input_repo, 
                                    output_repo = output_repo, 
                                    file_storage = file_storage, 
                                    parser = parser,
                                    steps_goal = steps_goal)
            
            #Execute the use case
TEST-->     report = use_case.execute(file_bytes = file_bytes, filename = filename)
            
            #Build the response mapping DOMAIN -> API schema (DTO)
            report_response = IngestReportResponse.from_domain(report)
            
            #Return the response (Pydantic model)
            return report_response

'''

#and inside the use case ingestdailycsv we have multiple dependencies that we will fake
'''
input_repo.save_input
input_repo.get_input

output_repo.save_output

file_storage.save_uploaded_csv
file_storage.move_csv_to_unprocessable
file_storage.move_csv_to_processed

parser.parse
'''


from datetime import datetime
from typing import List

from app.domain.entities import DailyMetricsInput, DailyKPIsOutput


class FakeFileStorage:
    def __init__(self):
        self.saved_files = []
        self.processed = []
        self.unprocessable = []

    def save_uploaded_csv(self, file_bytes: bytes, filename: str) -> str:
        file_id = f"fake://{filename}"
        self.saved_files.append((file_id, file_bytes))
        return file_id

    def move_csv_to_processed(self, file_id: str) -> str:
        self.processed.append(file_id)
        return file_id

    def move_csv_to_unprocessable(self, file_id: str) -> str:
        self.unprocessable.append(file_id)
        return file_id


class FakeCSVParser:
    def __init__(self, records: List[DailyMetricsInput]):
        self.records = records
        self.called_with = None

    def parse(self, file_bytes: bytes) -> List[DailyMetricsInput]:
        self.called_with = file_bytes
        return self.records


class FakeInputRepository:
    def __init__(self, existing_records: List[DailyMetricsInput]):
        self.saved_inputs = []
        self.existing_records = existing_records
        self.get_calls = []

    def save_input(self, input_data: List[DailyMetricsInput]) -> None:
        self.saved_inputs.extend(input_data)

    def get_input(self, start: datetime, end: datetime) -> List[DailyMetricsInput]:
        self.get_calls.append((start, end))
        return self.existing_records


class FakeOutputRepository:
    def __init__(self):
        self.saved_outputs = []

    def save_output(self, output_data: List[DailyKPIsOutput]) -> None:
        self.saved_outputs.extend(output_data)




from app.business.use_cases import IngestDailyCSV
from app.domain.entities import IngestReport


def test_ingest_empty_csv_marks_unprocessable():
    storage = FakeFileStorage()
    parser = FakeCSVParser(records=[])
    input_repo = FakeInputRepository(existing_records=[])
    output_repo = FakeOutputRepository()

    use_case = IngestDailyCSV(
        input_repo=input_repo,
        output_repo=output_repo,
        file_storage=storage,
        parser=parser,
    )

    report: IngestReport = use_case.execute(
        file_bytes=b"date,steps_n\n",
        filename="empty.csv",
    )

    assert report.status == "unprocessable"
    assert report.records_processed == 0
    assert report.kpi_records_upserted == 0
    assert storage.unprocessable == ["fake://empty.csv"]
    assert storage.processed == []
    assert input_repo.saved_inputs == []
    assert output_repo.saved_outputs == []


from datetime import datetime, timezone

from app.business.use_cases import IngestDailyCSV
from app.domain.entities import DailyMetricsInput


def test_ingest_happy_path_saves_inputs_and_outputs():
    record = DailyMetricsInput(
        date=datetime(2024, 1, 10, tzinfo=timezone.utc),
        steps_n=12000,
        proteins_g=120,
        kcal_in=2200,
        kcal_junk_in=200,
        kcal_out_training=400,
        sleep_hours=7.5,
        stress_rel=2,
        weight_kg=80.0,
        waist_cm=85.0,
    )

    storage = FakeFileStorage()
    parser = FakeCSVParser(records=[record])

    # context includes the same record (simplest valid case)
    input_repo = FakeInputRepository(existing_records=[record])
    output_repo = FakeOutputRepository()

    use_case = IngestDailyCSV(
        input_repo=input_repo,
        output_repo=output_repo,
        file_storage=storage,
        parser=parser,
        steps_goal=10000,
    )

    report = use_case.execute(
        file_bytes=b"fake csv bytes",
        filename="data.csv",
    )

    assert report.status == "processed"
    assert report.records_processed == 1
    assert report.kpi_records_upserted == 1

    # storage
    assert storage.processed == ["fake://data.csv"]
    assert storage.unprocessable == []

    # inputs
    assert input_repo.saved_inputs == [record]

    # outputs
    assert len(output_repo.saved_outputs) == 1
    assert output_repo.saved_outputs[0].date.date() == record.date.date()


def test_file_is_moved_to_processed_only_after_success():
    record = DailyMetricsInput(
        date=datetime(2024, 1, 5, tzinfo=timezone.utc),
        steps_n=8000,
        proteins_g=90,
        kcal_in=2000,
        kcal_junk_in=300,
        kcal_out_training=300,
        sleep_hours=6.5,
        stress_rel=3,
        weight_kg=81.0,
        waist_cm=86.0,
    )

    storage = FakeFileStorage()
    parser = FakeCSVParser(records=[record])
    input_repo = FakeInputRepository(existing_records=[record])
    output_repo = FakeOutputRepository()

    use_case = IngestDailyCSV(
        input_repo=input_repo,
        output_repo=output_repo,
        file_storage=storage,
        parser=parser,
    )

    use_case.execute(b"bytes", "file.csv")

    assert storage.saved_files
    assert storage.processed == ["fake://file.csv"]
    assert storage.unprocessable == []
