from app.infrastructure.db.base import Base
from app.infrastructure.db.engine import engine

from app.infrastructure.db import models

def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("smoke test OK: tables created (if they didn't exist)")
    

if __name__ == "__main__":
    main()