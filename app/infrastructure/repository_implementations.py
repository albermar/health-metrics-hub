from app.domain.interfaces import OutputRepository_Interface
from datetime import datetime
from app.domain.entities import DailyKPIsOutput
from sqlalchemy.orm import Session


class Postgres_OutputRepository(OutputRepository_Interface):
        """
        Implementation of OutputRepository_Interface for PostgreSQL.
        """        
        def __init__(self, db_session: Session):
            self._db = db_session
            
        def save_output(self, output_data: list[DailyKPIsOutput]) -> None :
            #TODO: Map DailyKPIsOutput to ORM model and save to DB
            pass      
        
        def get_output(self, start: datetime, end: datetime) -> list[DailyKPIsOutput]:
            #TODO: Query DB for KPIs in date range, map ORM models to DailyKPIsOutput entities and return
            pass
