# app/api/routes/auth.py
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

from app.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from app.core.config import get_db, settings
from app.models.tax_models import UserProfile
from app.schemas.tax_schemas import UserResponse

# Create router instance
router = APIRouter()


# Define models for the auth endpoints
class Token(BaseModel):
    """JWT token response model"""

    access_token: str
    token_type: str


class UserCreate(BaseModel):
    """User registration model"""

    email: EmailStr
    password: str
    name: str
    surname: str
    date_of_birth: str
    is_provisional_taxpayer: Optional[bool] = False

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserProfileUpdate(BaseModel):
    """User profile update model"""

    name: Optional[str] = None
    surname: Optional[str] = None
    date_of_birth: Optional[str] = None
    is_provisional_taxpayer: Optional[bool] = None


class PasswordChange(BaseModel):
    """Password change model"""

    current_password: str
    new_password: str

    @validator("new_password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        return v


class LoginResponse(BaseModel):
    """Login response model with user info and token"""

    access_token: str
    token_type: str
    user: Dict[str, Any]


# FIXED: Use the correct endpoint that frontend expects
@router.post("/login", response_model=LoginResponse)
async def login_user(email: str, password: str, db: Session = Depends(get_db)):
    """Alternative login endpoint for JSON requests."""
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    user_data = {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "surname": user.surname,
        "is_provisional_taxpayer": user.is_provisional_taxpayer,
        "is_admin": getattr(user, "is_admin", False),
    }

    return {"access_token": access_token, "token_type": "bearer", "user": user_data}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserProfile = Depends(get_current_user)):
    """Get the current user's profile based on JWT token."""
    return current_user


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and generate JWT token (OAuth2 compatible)."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    # Check if user already exists
    db_user = db.query(UserProfile).filter(UserProfile.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Convert string date to date object
    try:
        date_of_birth = datetime.strptime(user.date_of_birth, "%Y-%m-%d").date()
    except ValueError:
        # Try alternative date format
        try:
            date_of_birth = datetime.strptime(user.date_of_birth, "%Y/%m/%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD or YYYY/MM/DD"
            )

    # Validate date of birth is in the past
    if date_of_birth >= datetime.now().date():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Date of birth must be in the past")

    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    db_user = UserProfile(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name,
        surname=user.surname,
        date_of_birth=date_of_birth,
        is_provisional_taxpayer=user.is_provisional_taxpayer,
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"message": "User created successfully", "user_id": db_user.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating user: {str(e)}")


@router.put("/profile")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user profile."""
    try:
        # Update fields if provided
        if profile_data.name is not None:
            current_user.name = profile_data.name.strip()
        if profile_data.surname is not None:
            current_user.surname = profile_data.surname.strip()
        if profile_data.date_of_birth is not None:
            try:
                date_of_birth = datetime.strptime(profile_data.date_of_birth, "%Y-%m-%d").date()
            except ValueError:
                try:
                    date_of_birth = datetime.strptime(profile_data.date_of_birth, "%Y/%m/%d").date()
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid date format. Use YYYY-MM-DD or YYYY/MM/DD",
                    )

            if date_of_birth >= datetime.now().date():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Date of birth must be in the past")
            current_user.date_of_birth = date_of_birth

        if profile_data.is_provisional_taxpayer is not None:
            current_user.is_provisional_taxpayer = profile_data.is_provisional_taxpayer

        # Update timestamp
        current_user.updated_at = datetime.utcnow().date()

        db.commit()
        db.refresh(current_user)

        # Return updated user data
        return {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "surname": current_user.surname,
            "date_of_birth": current_user.date_of_birth.isoformat(),
            "is_provisional_taxpayer": current_user.is_provisional_taxpayer,
            "is_admin": getattr(current_user, "is_admin", False),
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating profile: {str(e)}"
        )


@router.put("/change-password")
async def change_user_password(
    password_data: PasswordChange, current_user: UserProfile = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Change user password."""
    from app.core.auth import get_password_hash, verify_password

    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    try:
        # Update password
        current_user.hashed_password = get_password_hash(password_data.new_password)
        current_user.updated_at = datetime.utcnow().date()

        db.commit()
        return {"message": "Password changed successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error changing password: {str(e)}"
        )


@router.post("/logout")
async def logout(response: Response):
    """Endpoint for client-side logout."""
    return {"message": "Successfully logged out"}
