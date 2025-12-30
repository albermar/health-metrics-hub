#This file has one single responsibility:
    #Define ONE Declarative Base → which owns ONE MetaData → which will collect ALL ORM tables
    #Every ORM model will do: class Something(Base) and all tables will be registered into Base.metadata
    #Base.metadata.create_all(engine) will work globally

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# you can add common methods or attributes for all ORM models here. For now, it's empty
