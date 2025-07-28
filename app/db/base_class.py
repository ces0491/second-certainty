# app/db/base_class.py
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def create_all(engine):
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
