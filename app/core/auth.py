# app/core/auth.py
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_db, settings
from app.models.tax_models import UserProfile

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to verify against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        The hashed password string
    """
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str) -> Optional[UserProfile]:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User's email address
        password: User's plain text password

    Returns:
        UserProfile if authentication successful, None otherwise
    """
    user = db.query(UserProfile).filter(UserProfile.email == email.lower()).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None

    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()

    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token (usually {"sub": email})
        expires_delta: Optional custom expiration time

    Returns:
        The encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify

    Returns:
        The email (subject) from the token if valid, None otherwise
    """
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


def get_current_user(token: str = Depends(security), db: Session = Depends(get_db)) -> UserProfile:
    """
    Get the current user from JWT token (HTTPBearer).

    Args:
        token: The HTTP Bearer token
        db: Database session

    Returns:
        The current UserProfile

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Extract token from HTTPBearer
        token_str = token.credentials if hasattr(token, "credentials") else str(token)

        payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(UserProfile).filter(UserProfile.email == email).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_user_oauth2(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserProfile:
    """
    Get the current user from JWT token (OAuth2PasswordBearer).
    Alternative method for OAuth2 compatibility.

    Args:
        token: The OAuth2 token
        db: Database session

    Returns:
        The current UserProfile

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(UserProfile).filter(UserProfile.email == email).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """
    Get the current active user.

    Args:
        current_user: The current user from get_current_user

    Returns:
        The current active UserProfile

    Raises:
        HTTPException: If user is inactive
    """
    if hasattr(current_user, "is_active") and not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_user(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """
    Get the current admin user.

    Args:
        current_user: The current user from get_current_user

    Returns:
        The current admin UserProfile

    Raises:
        HTTPException: If user is not an admin
    """
    if not hasattr(current_user, "is_admin") or not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


def create_user(
    db: Session,
    email: str,
    password: str,
    name: str,
    surname: str,
    date_of_birth,
    is_provisional_taxpayer: bool = False,
    is_admin: bool = False,
) -> UserProfile:
    """
    Create a new user in the database.

    Args:
        db: Database session
        email: User's email
        password: User's plain text password
        name: User's first name
        surname: User's last name
        date_of_birth: User's date of birth
        is_provisional_taxpayer: Whether user is a provisional taxpayer
        is_admin: Whether user is an admin

    Returns:
        The created UserProfile

    Raises:
        Exception: If user creation fails
    """
    hashed_password = get_password_hash(password)
    db_user = UserProfile(
        email=email.lower(),
        hashed_password=hashed_password,
        name=name,
        surname=surname,
        date_of_birth=date_of_birth,
        is_provisional_taxpayer=is_provisional_taxpayer,
        is_admin=is_admin,
        created_at=datetime.utcnow().date(),
        updated_at=datetime.utcnow().date(),
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_password(db: Session, user: UserProfile, new_password: str) -> bool:
    """
    Update a user's password.

    Args:
        db: Database session
        user: The user to update
        new_password: The new plain text password

    Returns:
        True if successful, False otherwise
    """
    try:
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow().date()
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


def check_email_exists(db: Session, email: str) -> bool:
    """
    Check if an email address already exists in the database.

    Args:
        db: Database session
        email: Email address to check

    Returns:
        True if email exists, False otherwise
    """
    user = db.query(UserProfile).filter(UserProfile.email == email.lower()).first()
    return user is not None
