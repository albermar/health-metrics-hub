from app.domain.entities import DailyKPIsOutput
from app.domain.interfaces import OutputRepository_Interface
from app.infrastructure.db.models import DailyKPIORM

from datetime import datetime, timezone, time
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
            
            #I assume here we receibe an active DB session from outside. Not sure where yet. 
            try:
                #for each KPI in output_data, check if exists, then insert or update
                for kpi in output_data:
                    #Extract date to check if record exists
                    day_to_check = kpi.date.date()  # Assuming kpi.date is a datetime object. the method .date() extracts the date part only. It's a datetime method and a common operation when dealing with datetime objects.
                    
                    #we build the select statement to talk to the DB. The goal is to obtain the row if exists or None if not. The professional way is using these following methods:
                    # First, we build the select statement:
                    statement = select(DailyKPIORM).where(DailyKPIORM.day == day_to_check)
                    # Then, we execute the statement and fetch one or none:
                    existing_row = self._db.execute(statement).scalar_one_or_none()
                    
                    if not existing_row:
                        #Insert new row:
                        # 1. Create an ORM instance
                        # 2. Add to the session (not yet committed)
                        # 3. Commit the session after the loop, so we do it in batch. Good for performance.
                        new_row = DailyKPIORM(
                            day = day_to_check,
                            neat_from_steps = kpi.neat_from_steps,
                            basal_spend = kpi.basal_spend,
                            balance_kcal = kpi.balance_kcal,
                            balance_7d_average = kpi.balance_7d_average,
                            computed_at = datetime.now(timezone.utc)
                        )
                        self._db.add(new_row)
                    else:
                        #Update existing row:
                        # In this case the variable existing_row is already the ORM instance we fetched from the DB. We just need to update its attributes.
                        existing_row.neat_from_steps = kpi.neat_from_steps
                        existing_row.basal_spend = kpi.basal_spend
                        existing_row.balance_kcal = kpi.balance_kcal
                        existing_row.balance_7d_average = kpi.balance_7d_average
                        existing_row.computed_at = datetime.now(timezone.utc) 
                        # No need to add to session again, it's already being tracked.
                        # What would happen if we add it again? SQLAlchemy would ignore it since it's already in the session. No error, but unnecessary.
                        #we could delete and re-add, but it's not needed. If we wanted to do that, it would be like:
                        #self._db.delete(existing_row)
                        #self._db.add(existing_row)
                        # But again, not needed here. Just commenting for learning purposes so it sticks better in mind.
                #After processing all KPIs, commit the session to persist changes
                self._db.commit()
            
            #if while looping through the KPIs an error occurs, we rollback the session to avoid partial commits. All or none
            except Exception as e:
                self._db.rollback()
                raise                
            
        
        def get_output(self, start: datetime, end: datetime) -> list[DailyKPIsOutput]:
            #TODO: Query DB for KPIs in date range, map ORM models to DailyKPIsOutput entities and return
            
            #the goal is to return a list of domain entities (DailyKPIsOutput) from the DB rows
            #step 1: build the select statement
            #step 2: execute and fetch all rows. Maybe there are unexisting rows in the range, so we just get what exists.
            #step 3: the statement will return ORM instances. We need to map them to domain entities. We will do this through a simple loop.
            #step 4: return the list of domain entities
            #step 5: handle exceptions if any
            #step 6: ensure the DB session is properly managed (committed/rolled back) if needed
            
            #we define an empty list to hold the domain entities.
            domain_entities:list[DailyKPIsOutput] = []
            
            try:
                statement = (
                            select(DailyKPIORM)
                            .where(DailyKPIORM.day >= start.date(), DailyKPIORM.day <= end.date())
                            .order_by(DailyKPIORM.day.asc())
                            )
                result = self._db.execute(statement) #this can return multiple rows, 1 row or none                
                orm_rows = result.scalars().all()                
                #scalars() means: we want the ORM instances, not the full result objects
                #all() means: fetch all rows as a list. This will return an empty list if no rows found, which is fine.
                
                #now we have a list of ORM instances. We need to map them to domain entities.
                
                for orm_row in orm_rows: #If empty this loop is skipped, no worries.
                    #map each orm_row to DailyKPIsOutput
                    #Create a new domain entity. Question: do we have a constructor that accepts parameters? Yes, because we used decorator @dataclass, so:
                    kpi = DailyKPIsOutput(
                        date=datetime.combine(orm_row.day, time.min, tzinfo=timezone.utc),
                        neat_from_steps=orm_row.neat_from_steps,
                        basal_spend=orm_row.basal_spend,
                        balance_kcal=orm_row.balance_kcal, 
                        balance_7d_average=orm_row.balance_7d_average
                    )             
                    #append to the list
                    domain_entities.append(kpi)                
                #after the loop we may have a list of domain entities or an empty list if no rows found 
                           
            except Exception:
                #selff._db.rollback() Rollback not needed here, we are just reading
                raise
            finally:
                #selff._db.close() Not here, the session should be managed outside. IMPORTANT                
                ...
            return domain_entities
                
            
