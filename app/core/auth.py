# app/core/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel, validator
from typing import Optional

from app.core.database import get_db
from app.models.user import UserProfile
from app.core.auth import authenticate_user, create_access_token, get_password_hash, get_current_user, verify_password
from app.schemas.tax_schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

class UserRegistration(BaseModel):
    """User registration model"""
    email: str
    password: str
    name: str
    surname: str
    date_of_birth: str
    is_provisional_taxpayer: bool = False
    
    @validator('email')
    def email_must_be_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        try:
            date_obj = datetime.strptime(v, "%Y-%m-%d").date()
            if date_obj >= datetime.now().date():
                raise ValueError('Date of birth must be in the past')
            return v
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError('Invalid date format. Use YYYY-MM-DD')
            raise e

class UserLogin(BaseModel):
    """User login model"""
    email: str
    password: str

class UserUpdate(BaseModel):
    """User profile update model"""
    name: Optional[str] = None
    surname: Optional[str] = None
    date_of_birth: Optional[str] = None
    is_provisional_taxpayer: Optional[bool] = None
    
    @validator('name', 'surname')
    def validate_names(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Name fields cannot be empty')
        return v.strip() if v else v
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if v is not None:
            try:
                date_obj = datetime.strptime(v, "%Y-%m-%d").date()
                if date_obj >= datetime.now().date():
                    raise ValueError('Date of birth must be in the past')
                return v
            except ValueError as e:
                if "time data" in str(e):
                    raise ValueError('Invalid date format. Use YYYY-MM-DD')
                raise e
        return v

class PasswordChange(BaseModel):
    """Password change model"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str
    user: UserResponse

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserRegistration, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Creates a new user with the provided information and returns the user data.
    Email addresses must be unique.
    """
    # Check if user already exists
    existing_user = db.query(UserProfile).filter(UserProfile.email == user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        # Convert string date to date object
        date_of_birth = datetime.strptime(user_data.date_of_birth, "%Y-%m-%d").date()
        
        # Create new user
        new_user = UserProfile(
            email=user_data.email.lower(),
            hashed_password=get_password_hash(user_data.password),
            name=user_data.name,
            surname=user_data.surname,
            date_of_birth=date_of_birth,
            is_provisional_taxpayer=user_data.is_provisional_taxpayer,
            created_at=datetime.utcnow().date(),
            updated_at=datetime.utcnow().date()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=LoginResponse)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token.
    
    Validates user credentials and returns a JWT access token for authenticated requests.
    """
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserProfile = Depends(get_current_user)):
    """
    Get the current user's profile information.
    
    Returns the profile data for the authenticated user.
    """
    return current_user

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Update the current user's profile information.
    
    Users can update their name, surname, date of birth, and provisional taxpayer status.
    Email cannot be changed for security reasons.
    """
    try:
        # Convert string date to date object if provided
        if profile_data.date_of_birth:
            if isinstance(profile_data.date_of_birth, str):
                profile_data.date_of_birth = datetime.strptime(profile_data.date_of_birth, "%Y-%m-%d").date()
        
        # Update the user's profile
        for field, value in profile_data.dict(exclude_unset=True).items():
            if hasattr(current_user, field) and field != 'email':  # Prevent email changes
                setattr(current_user, field, value)
        
        # Update the updated_at timestamp
        current_user.updated_at = datetime.utcnow().date()
        
        db.commit()
        db.refresh(current_user)
        
        return current_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )

@router.put("/change-password")
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Change the current user's password.
    
    Requires the current password for verification and a new password.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    try:
        # Hash the new password and update
        current_user.hashed_password = get_password_hash(password_data.new_password)
        current_user.updated_at = datetime.utcnow().date()
        
        db.commit()
        
        return {"message": "Password changed successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing password: {str(e)}"
        )

@router.post("/logout")
async def logout(response: Response):
    """
    Endpoint for client-side logout.
    
    This is primarily for documentation purposes as JWT tokens
    cannot be invalidated - the client should remove the token.
    """
    return {"message": "Successfully logged out"}