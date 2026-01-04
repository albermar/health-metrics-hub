from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    Text,
    select,
    insert,
)

DATABASE_URL = "postgresql+psycopg://alberto:supersecret@localhost:5432/health_drill"

metadata = MetaData()

notes = Table(
    "notes_core",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("text", Text, nullable=False),
)

def main() -> None:
    engine = create_engine(DATABASE_URL, echo=True)

    # Create table if it does not exist
    metadata.create_all(engine)

    # Give me one active database connection from the pool
    with engine.begin() as conn:
        # Insert a row
        result = conn.execute(insert(notes).values(text="hello from sqlalchemy core"))
        
        inserted_id = result.inserted_primary_key[0]
        
        # Select it back
        stmt = select(notes).where(notes.c.id == inserted_id)
        row = conn.execute(stmt).one()

        print("Inserted and fetched:", row)

if __name__ == "__main__":
    main()
