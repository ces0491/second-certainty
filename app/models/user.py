from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import date, datetime

from app.core.database import Base

class UserProfile(Base):
    """
    User profile model for storing user account information.
    
    This model represents a user in the Second Certainty tax management system,
    storing personal information, authentication details, and tax-related preferences.
    """
    __tablename__ = "user_profiles"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Personal information
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    
    # Tax-related information
    is_provisional_taxpayer = Column(Boolean, default=False, nullable=False)
    
    # Admin and status fields
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(Date, default=date.today, nullable=False)
    updated_at = Column(Date, default=date.today, onupdate=date.today, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Optional fields for future enhancements
    phone_number = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    tax_reference_number = Column(String(20), nullable=True)
    
    # Relationships (these will be defined when other models are created)
    # incomes = relationship("Income", back_populates="user", cascade="all, delete-orphan")
    # expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    # provisional_taxes = relationship("ProvisionalTax", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserProfile(id={self.id}, email='{self.email}', name='{self.name} {self.surname}')>"
    
    def __str__(self):
        return f"{self.name} {self.surname} ({self.email})"
    
    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.name} {self.surname}"
    
    @property
    def age(self) -> int:
        """Calculate and return the user's age based on date of birth."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def update_last_login(self):
        """Update the last login timestamp to current time."""
        self.last_login = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """
        Convert user object to dictionary for API responses.
        
        Returns:
            dict: User data excluding sensitive information
        """
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "surname": self.surname,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "is_provisional_taxpayer": self.is_provisional_taxpayer,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "full_name": self.full_name,
            "age": self.age
        }