# init_db.py
from app.models.tax_models import Base
from app.core.config import engine

def init_db():
    print('Creating database tables...')
    Base.metadata.create_all(bind=engine)
    print('Database tables created successfully!')

if __name__ == '__main__':
    init_db()
