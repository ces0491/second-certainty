# app/api/routes/auth.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator

from app.core.auth import authenticate_user, create_access_token, get_password_hash, get_current_user
from app.core.config import settings, get_db
from app.models.tax_models import UserProfile
from app.schemas.tax_schemas import UserResponse

# Create router instance - this must be defined before any routes
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
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class LoginResponse(BaseModel):
    """Login response model with user info and token"""
    access_token: str
    token_type: str
    user: Dict[str, Any]

# Endpoints
@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserProfile = Depends(get_current_user)):
    """
    Get the current user's profile based on JWT token.
    
    This endpoint requires authentication via Bearer token.
    """
    return current_user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and generate JWT token.
    
    Returns access token for use in Authentication header.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Returns success message if registration is successful.
    """
    # Check if user already exists
    db_user = db.query(UserProfile).filter(UserProfile.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Convert string date to date object
    try:
        date_of_birth = datetime.strptime(user.date_of_birth, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    db_user = UserProfile(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name,
        surname=user.surname,
        date_of_birth=date_of_birth,
        is_provisional_taxpayer=user.is_provisional_taxpayer
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"message": "User created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/logout")
async def logout(response: Response):
    """
    Endpoint for client-side logout.
    
    This is primarily for documentation purposes as JWT tokens
    cannot be invalidated - the client should remove the token.
    """
    return {"message": "Successfully logged out"}