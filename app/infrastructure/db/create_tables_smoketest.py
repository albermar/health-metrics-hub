'''
Deprecated: use Alembic migrations instead.
Simple smoketest script to create DB tables.
'''



from app.infrastructure.db.base import Base
from app.infrastructure.db.engine import engine 

import app.infrastructure.db.models

def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("smoke test OK: tables created (if they didn't exist)")
    

if __name__ == "__main__":
    main()