from app.domain.interfaces import OutputRepository_Interface
from datetime import datetime
from app.domain.entities import DailyKPIsOutput
from sqlalchemy.orm import Session


#Check this: 
# Where is this function used? in the router
# Is there a DB session available here? --> No, we would need to create one or use Dependency Injection
# Flow example: 
# Router -> Build Repo (with DB session) -> Build Use Case (with Repo) -> Execute Use Case
# So the DB session should be created in the router or passed down from a higher level (e.g., middleware)
# For simplicity, we will not handle DB session creation here. In a real app, use Dependency Injection or a session manager.
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
