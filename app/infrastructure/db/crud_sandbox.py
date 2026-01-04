from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.infrastructure.db.engine import SessionLocal
from app.infrastructure.db.models import DailyInputORM


def _print_row(row: DailyInputORM, label: str) -> None:
    print(
        f"{label}: id={row.id} day={row.day} steps={row.steps} "
        f"cal_in={row.calories_in} cal_out={row.calories_out} source={row.source}"
    )


def main() -> None:
    # 1) Create a new Session (one unit of work)
    db = SessionLocal()
    '''
    Remember:
    db = SessionLocal()
    try:
    except Exception as e:
    finally:
        db.close()
    
    '''

    try:        
        target_day = date(2026, 1, 2)

        # 2) CREATE (insert)
        print("\n--- CREATE ---")        
        
        # Create the candidate. New Python object in memory (not DB)
        row = DailyInputORM(
            day=target_day,
            steps=8000,
            calories_in=2300,
            calories_out=2600,
            weight_kg=86.5,
            sleep_hours=7.0,
            source="crud_sandbox",
        )
        _print_row(row, "before flush")        
        # Add to session or Staged inside the session (marks for insert)... Think of it as a “to do” list, like this is something I plan to insert...
        db.add(row)

        # Flush sends SQL but does NOT commit yet. Unnecesary here but shown for demo purposes. commit() would do both flush+commit together. 
        db.flush()
        _print_row(row, "After flush (id assigned, not committed)")

        db.commit()  # Now it's permanent
        db.refresh(row)  # Reload from DB to be sure that the object reflects what's actually stored...
        
        _print_row(row, "After commit")

        # 3) READ (query)
        print("\n--- READ ---")
        stmt = select(DailyInputORM).where(DailyInputORM.day == target_day)
        found = db.execute(stmt).scalar_one() # expect exactly one result, error if 0 or >1. Since day is unique in our schema, exactly one is expected.
        
        _print_row(found, "Queried")
        print(f"Type of found object: {type(found)}")

        # 4) UPDATE
        print("\n--- UPDATE ---")
        found.steps = 9999
        found.source = "updated_in_sandbox"
        db.commit()
        db.refresh(found)
        _print_row(found, "After update commit")


        # 5) DELETE
        print("\n--- DELETE ---")
        db.delete(found)
        db.commit()
        print("Deleted and committed.")

        # 6) Confirm it's gone
        print("\n--- CONFIRM DELETE ---")
        maybe = db.execute(stmt).scalar_one_or_none()
        print("Result:", maybe)
      
        #print the whole table for visual confirmation
        print("\n--- CURRENT TABLE CONTENTS ---")
        all_rows = db.execute(select(DailyInputORM)).scalars().all()
        for r in all_rows:
            _print_row(r, "Row")


    except Exception as e:
        # If anything fails, rollback so we don't leave partial work
        db.rollback()
        print("\n❌ Error occurred, rolled back.")
        raise
    finally:
        db.close()
        print("\nSession closed.")


if __name__ == "__main__":
    main()
