# create_admin.py
import sys
import os
from datetime import date
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.config import get_db
from app.models.tax_models import UserProfile
from app.core.auth import get_password_hash

def create_admin_user(email, password, name, surname):
    """Create an admin user directly in the database."""
    db = next(get_db())
    try:
        # Check if user already exists
        existing_user = db.query(UserProfile).filter(UserProfile.email == email).first()
        if existing_user:
            print(f"User with email {email} already exists. Setting as admin...")
            existing_user.is_admin = True
            db.commit()
            print(f"User {email} is now an admin.")
            return
            
        # Create new admin user
        hashed_password = get_password_hash(password)
        
        new_user = UserProfile(
            email=email,
            hashed_password=hashed_password,
            name=name,
            surname=surname,
            date_of_birth=date(1990, 1, 1),  # Default date, change as needed
            is_provisional_taxpayer=False,
            is_admin=True,
        )
        
        db.add(new_user)
        db.commit()
        print(f"Admin user {email} created successfully.")
            
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python create_admin.py <email> <password> <first_name> <last_name>")
        sys.exit(1)
        
    email = sys.argv[1]
    password = sys.argv[2]
    name = sys.argv[3]
    surname = sys.argv[4]
    
    create_admin_user(email, password, name, surname)