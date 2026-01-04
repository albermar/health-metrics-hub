from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import Integer, Text, select

DATABASE_URL = "postgresql+psycopg://alberto:supersecret@localhost:5432/health_drill"


# 1. Base class for ORM models
class Base(DeclarativeBase):
    pass


# 2. ORM model = table mapping
class Note(Base):
    __tablename__ = "notes_orm"

    id:     Mapped[int] = mapped_column(Integer, primary_key=True)
    text:   Mapped[str] = mapped_column(Text, nullable=False)


def main() -> None:
    # 3. Engine (same concept as Core)
    engine = create_engine(DATABASE_URL, echo=True)

    # 4. Create tables
    Base.metadata.create_all(engine)

    # 5. Session factory
    Session = sessionmaker(bind=engine)

    # 6. ORM work unit
    with Session() as session:
        # Create object
        note = Note(text="hello from sqlalchemy orm")
        session.add(note)
        
        # Persist (commit transaction)
        session.commit()

        # Query back
        stmt = select(Note).where(Note.id == note.id)
        result = session.execute(stmt).scalar_one()

        print("Inserted and fetched:", result.id, result.text)


if __name__ == "__main__":
    main()
