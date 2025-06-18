"""
Database initialization script for Second Certainty Tax Tool.

This script creates all necessary database tables and can optionally
seed the database with initial data.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database import create_tables, engine
from app.models.user import UserProfile
from app.models.income import Income
from app.models.expense import Expense
from app.models.provisional_tax import ProvisionalTax

def init_database():
    """
    Initialize the database by creating all tables.
    """
    print("🔧 Initializing Second Certainty database...")
    
    try:
        # Import all models to ensure they're registered with SQLAlchemy
        print("📋 Importing database models...")
        
        # Create all tables
        print("🏗️  Creating database tables...")
        create_tables()
        
        print("✅ Database initialization completed successfully!")
        print(f"🗄️  Database engine: {engine.url}")
        
        # Check if tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if tables:
            print(f"📊 Created tables: {', '.join(tables)}")
        else:
            print("⚠️  Warning: No tables found after creation")
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)

def check_database_connection():
    """
    Check if we can connect to the database.
    """
    try:
        # Test database connection
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print(f"✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Second Certainty Tax Tool - Database Setup")
    print("=" * 50)
    
    # Check environment variables
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print(f"🌐 Using database: {db_url.split('@')[-1] if '@' in db_url else 'PostgreSQL'}")
    else:
        print("💾 Using SQLite database (development mode)")
    
    # Check database connection
    if not check_database_connection():
        print("\n💡 Tips for fixing database connection issues:")
        print("   - Ensure PostgreSQL is running (if using PostgreSQL)")
        print("   - Check DATABASE_URL environment variable")
        print("   - Verify database credentials")
        sys.exit(1)
    
    # Initialize database
    init_database()
    
    print("\n🎉 Setup complete! You can now start the application with:")
    print("   uvicorn app.main:app --reload")
    print("\n📚 Don't forget to run the seed script to populate initial data:")
    print("   python scripts/seed_data.py")