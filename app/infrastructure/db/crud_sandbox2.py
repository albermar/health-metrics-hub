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

from sqlalchemy import select

#We're going to use a specific databse just for practice and drill, called db_drills_1. So we're going to create a drill engine right here:

DRILLS_DB_NAME = 'db_drills_1'
DATABASE_URL = f"postgresql+psycopg://alberto:password1@localhost:5433/{DRILLS_DB_NAME}"

#create engine (tunnel to the database server)
drills_engine = create_engine(DATABASE_URL, echo=False)

#sessionmaker
DrillsSessionLocal = sessionmaker(
    bind = drills_engine,
    autocommit=False,
    autoflush=False
)
def get_row_by_day(db, day:date)-> DailyInputORM | None:
    statement = select(DailyInputORM).where(DailyInputORM.day == day)
    return db.execute(statement).scalar_one_or_none()

def cleanup_by_day(db, day:date) -> None:
    existing = get_row_by_day(db, day)
    if existing:
        db.delete(existing)
        db.commit()

def drill_1_insert_rollback(db):
    #we assume db is an openned session
    d1 = date(2024,6,1)
    cleanup_by_day(db, d1)
    
    print("Drill 1: insert + rollback")
    new_entry = DailyInputORM(
        day = d1,
        steps = 10001,
        calories_in = 2001,
        calories_out = 2501,
        weight_kg = 81.5,
        sleep_hours = 7.5,
        waist_cm = 90.0,
        chest_cm = 100.0,
        abdomen_cm = 95.0,
        source = "drill_1_test"        
    )
    db.add(new_entry)
    db.flush() #send to DB but not commit yet
    print("Flush: Inserted new entry with id:", new_entry.id) 
    
    db.rollback()
    
    again = get_row_by_day(db, d1)
    print("After rollback, entry is:", again) #should be None

def drill_2_unique_constraint_violation(db):
    print("Drill 2: unique constraint violation")
    d1 = date(2024,6,2)
    cleanup_by_day(db, d1)
    entry1 = DailyInputORM(
        day = d1,
        steps = 12000,
        source = "drill_2_test_1"
    )
    db.add(entry1)
    db.commit()
    print("Inserted first entry with id:", entry1.id)
    
    #now, try to insert another with same day, expect to fail
    try:
        entry2 = DailyInputORM(
            day = d1,
            steps = 13000,
            source = "drill_2_test_2"
        )
        db.add(entry2)    
        db.commit()
    except Exception as e:
        print("Expected exception on unique constraint violation:", e)
        db.rollback()
    stored = get_row_by_day(db, d1)
    print("Stored steps after violation attempt is:", stored.steps if stored else None) #should be entry1 only

def drill_3_update_field(db):
    print("\n\nDrill 3: update 1 field")
    d1 = date(2026, 1, 2)
    cleanup_by_day(db, d1)
    
    row = DailyInputORM(day=d1, steps=3333, source="drill_3")
    db.add(row)
    db.commit()
    print("inserted steps = ", row.steps)
    
    found = get_row_by_day(db, d1)
    print("Before update steps =", found.steps)
    
    found.steps = 3334
    db.commit() #found is a referenced object, so just commit
    
    updated = get_row_by_day(db, d1)
    print("After update steps =", updated.steps)
    
    
def drill_4_delete_query(db):
    print("\n\nDrill 4: delete then query")
    d1 = date(2026, 1, 2)
    cleanup_by_day(db, d1)
    
    row = DailyInputORM(day=d1, steps=4444, source="drill4")
    db.add(row)
    db.commit()
    print("inserted id = ", row.id)
    
    to_delete = get_row_by_day(db, d1)
    db.delete(to_delete)
    print("Deleted staged (NOT committed yet).")

    # In the same session, ORM considers it deleted, so query often returns None.
    inside = get_row_by_day(db, d1)
    print("Query in SAME session before commit ->", inside)
    
    # Rollback should undo the delete
    db.rollback()
    restored = get_row_by_day(db, d1)
    print("After rollback, row exists again? ->", restored is not None)
    
    # Now delete for real
    db.delete(restored)
    db.commit()
    gone = get_row_by_day(db, d1)
    print("After delete commit, query should be None ->", gone)

    print("\n✅ All drills finished successfully.")
        
        
if __name__ == "__main__":
    print("Starting drills with SQLAlchemy ORM + Postgres...")
    Base.metadata.create_all(bind = drills_engine) #create tables in drills_db_1 database if not exist
    
    print("Creating drill DB session...")
    db = DrillsSessionLocal() #We use the drills engine, ensuring connect to this database
    
    #.... now let's code here drills etc... coming next    
    try:
        db_name = db.execute(text("SELECT current_database()")).scalar_one()
        print("Connected to:", db_name)
        print("ready for drills...")
        drill_1_insert_rollback(db)
        drill_2_unique_constraint_violation(db)
        drill_3_update_field(db)
        drill_4_delete_query(db)
    except Exception as e:
        print("Exception during drill:", e)
        db.rollback()
        raise
    finally:
        print("Closing drill DB session")
        db.close()
    
    
    