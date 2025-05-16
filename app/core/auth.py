# app/core/auth.py
from datetime import datetime, timedelta
from typing import Optional
import logging

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.tax_models import UserProfile
from app.core.config import settings
from app.core.config import get_db

# Set up logging
logger = logging.getLogger("auth")
logger.setLevel(logging.DEBUG)

# Patch bcrypt issue
import bcrypt
if not hasattr(bcrypt, '__about__'):
    bcrypt.__about__ = type('obj', (object,), {
        '__version__': getattr(bcrypt, 'VERSION', '3.2.0')
    })

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def verify_password(plain_password, hashed_password):
    logger.debug(f"Verifying password (plain length: {len(plain_password)})")
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, email: str, password: str):
    logger.debug(f"Authenticating user: {email}")
    user = db.query(UserProfile).filter(UserProfile.email == email).first()
    if not user:
        logger.warning(f"User not found: {email}")
        return False
    if not hasattr(user, 'hashed_password'):
        logger.error(f"User {email} has no hashed_password attribute")
        return False
    
    # Better error handling for password verification
    try:
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user: {email}")
            return False
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False
    
    logger.info(f"User authenticated successfully: {email}")
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    try:
        logger.debug(f"Creating token for {data.get('sub')} with expiry {expire}")
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {str(e)}")
        raise

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        logger.debug("Decoding JWT token")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise credentials_exception
    
    user = db.query(UserProfile).filter(UserProfile.email == email).first()
    if user is None:
        logger.warning(f"User not found for email: {email}")
        raise credentials_exception
    
    logger.debug(f"Successfully authenticated user: {email}")
    return user