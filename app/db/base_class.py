# app/db/base_class.py
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Add to app/db/base_class.py

def create_all(engine):
    """Create all tables."""
    Base.metadata.create_all(bind=engine)