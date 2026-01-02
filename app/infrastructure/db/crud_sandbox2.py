'''
Let's do 4 drills using SQLAlchemy ORM with PostgreSQL:
1. insert + rollback
2. unique constrint violation
3. update 1 field
4. delete and then query
'''

from app.infrastructure.db.base import Base
from app.infrastructure.db.models import DailyInputORM

from sqlalchemy import text

from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

#We're going to use a specific databse just for practice and drill, called db_drills_1. So we're going to create a drill engine right here:

DRILLS_DB_NAME = 'db_drills_1'
DATABASE_URL = f"postgresql+psycopg://alberto:password1@localhost:5432/{DRILLS_DB_NAME}"

#create engine (tunnel to the database server)
drills_engine = create_engine(DATABASE_URL, echo=False)

#sessionmaker
DrillsSessionLocal = sessionmaker(
    bind = drills_engine,
    autocommit=False,
    autoflush=False
)


if __name__ == "__main__":
    Base.metadata.create_all(bind = drills_engine) #create tables in drills_db_1
    
    db = DrillsSessionLocal() #We use the drills engine, ensuring connect to this database
    #.... now let's code here drills etc... coming next
    
    try:        
        db_name = db.execute(text("SELECT current_database()")).scalar_one()
        print("Connected to:", db_name)
        print("ready for drills...")
    except Exception as e:
        print("Exception during drill:", e)
        db.rollback()
    finally:
        print("Closing drill DB session")
        db.close()
        