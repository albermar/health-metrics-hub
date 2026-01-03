from app.domain.entities import DailyKPIsOutput
from app.domain.interfaces import OutputRepository_Interface
from app.infrastructure.db.models import DailyKPIORM

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select


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
            #for each day KPI in output_data: query existing KPI row by day. If exists, update it. If not, insert new row.
            try:
                for kpi in output_data:
                    #Extract date to check if record exists
                    day_value = kpi.date.date()  # Assuming kpi.date is a datetime object. the method .date() extracts the date part only.
                    statement = select(DailyKPIORM).where(DailyKPIORM.day == day_value)
                    existing_row = self._db.execute(statement).scalar_one_or_none()
                    
                    if not existing_row:
                        #Insert new row:
                        new_row = DailyKPIORM(
                            day = day_value,
                            neat_from_steps = kpi.neat_from_steps,
                            basal_spend = kpi.basal_spend,
                            balance_kcal = kpi.balance_kcal,
                            balance_7d_average = kpi.balance_7d_average,
                            computed_at = datetime.now(timezone.utc)
                        )
                        self._db.add(new_row)
                    else:
                        #Update existing row:
                        existing_row.neat_from_steps = kpi.neat_from_steps
                        existing_row.basal_spend = kpi.basal_spend
                        existing_row.balance_kcal = kpi.balance_kcal
                        existing_row.balance_7d_average = kpi.balance_7d_average
                        existing_row.computed_at = datetime.now(timezone.utc)
                self._db.commit()
            except Exception as e:
                self._db.rollback()
                raise
                
            
        
        def get_output(self, start: datetime, end: datetime) -> list[DailyKPIsOutput]:
            #TODO: Query DB for KPIs in date range, map ORM models to DailyKPIsOutput entities and return
            pass
