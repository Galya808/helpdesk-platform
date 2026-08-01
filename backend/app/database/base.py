from sqlalchemy.orm import DeclarativeBase


# All future models will inherit this model
# Base.metadata will contain the description of all registered tables
class Base(DeclarativeBase):
    pass