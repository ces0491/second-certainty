# add_admin_field.py
import sys
import os
from sqlalchemy import Column, Boolean, inspect, text
from sqlalchemy.exc import OperationalError

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.config import engine, get_db
from app.models.tax_models import UserProfile, Base

def add_admin_field():
    """Add is_admin field to user_profiles table using SQLAlchemy."""
    print("Adding is_admin field to UserProfile table...")
    
    # Get a database inspector to check the schema
    inspector = inspect(engine)
    
    # Connect to the database
    conn = engine.connect()
    
    try:
        # Check if the column already exists
        columns = [column['name'] for column in inspector.get_columns('user_profiles')]
        
        if "is_admin" not in columns:
            print("Column doesn't exist - adding it now...")
            
            # Different syntax for different database types
            if engine.name == 'sqlite':
                # SQLite syntax
                conn.execute(text("ALTER TABLE user_profiles ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            else:
                # PostgreSQL syntax
                conn.execute(text("ALTER TABLE user_profiles ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
            
            # Commit the transaction
            conn.commit()
            print("is_admin field added successfully")
            
            # Set the first user as admin (optional)
            conn.execute(text("UPDATE user_profiles SET is_admin = 1 WHERE id = 1"))
            conn.commit()
            print("First user set as admin")
        else:
            print("is_admin field already exists")
            
    except OperationalError as e:
        print(f"Database error adding is_admin field: {e}")
        
        # If the table doesn't exist yet, create all tables
        if "no such table" in str(e).lower():
            print("Tables don't exist yet - creating all tables...")
            Base.metadata.create_all(bind=engine)
            print("Database tables created")
            
            # Now let's try again with the new table
            try:
                if engine.name == 'sqlite':
                    conn.execute(text("ALTER TABLE user_profiles ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
                else:
                    conn.execute(text("ALTER TABLE user_profiles ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
                conn.commit()
                print("is_admin field added successfully")
            except Exception as e2:
                print(f"Error adding column after table creation: {e2}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        conn.close()

def make_user_admin(email):
    """Set a specific user as admin by email."""
    db = next(get_db())
    try:
        # First check if the column exists, if not add it
        add_admin_field()
        
        # Find user by email and make them admin
        result = db.execute(text(f"UPDATE user_profiles SET is_admin = 1 WHERE email = :email"), 
                          {"email": email})
        db.commit()
        
        # Check if any rows were affected
        if result.rowcount > 0:
            print(f"User with email {email} is now an admin")
        else:
            print(f"User with email {email} not found")
            
    except Exception as e:
        print(f"Error making user admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If email provided, make that user an admin
        make_user_admin(sys.argv[1])
    else:
        # Otherwise just add the field
        add_admin_field()
        print("\nTo make a specific user an admin, run: python add_admin_field.py user@example.com")