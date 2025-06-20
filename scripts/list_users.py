# list_users.py
import os
import sys

from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.config import get_db
from app.models.tax_models import UserProfile


def list_all_users():
    """List all registered users in the database."""
    db = next(get_db())
    try:
        users = db.query(UserProfile).all()

        if not users:
            print("No users found in the database.")
            return

        print(f"Found {len(users)} users:")
        for user in users:
            print(f"ID: {user.id}, Email: {user.email}, Name: {user.name} {user.surname}")

    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    list_all_users()
