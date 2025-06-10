from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import date, datetime
from decimal import Decimal

from app.core.database import Base

class Income(Base):
    """
    Income model for storing user income records.
    
    This model represents income entries for users in the tax management system,
    including various types of income sources such as salary, freelance work,
    investments, and other taxable income.
    """
    __tablename__ = "incomes"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False, index=True)
    
    # Income details
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    date_received = Column(Date, nullable=False)
    
    # Income categorization
    income_type = Column(String(50), nullable=False, index=True)
    # Common income types: 'salary', 'freelance', 'investment', 'rental', 'business', 'other'
    
    # Optional fields
    source = Column(String(255), nullable=True)  # Company/client name
    reference_number = Column(String(100), nullable=True)  # Invoice number, etc.
    notes = Column(Text, nullable=True)
    
    # Tax-related fields
    tax_deducted = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    is_taxable = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(Date, default=date.today, nullable=False)
    updated_at = Column(Date, default=date.today, onupdate=date.today, nullable=False)
    
    # Relationship
    # user = relationship("UserProfile", back_populates="incomes")

    def __repr__(self):
        return f"<Income(id={self.id}, user_id={self.user_id}, amount={self.amount}, type='{self.income_type}')>"
    
    def __str__(self):
        return f"{self.description}: R{self.amount:,.2f} ({self.income_type})"
    
    @property
    def net_amount(self) -> Decimal:
        """Calculate net amount after tax deductions."""
        return self.amount - (self.tax_deducted or Decimal('0'))
    
    def to_dict(self) -> dict:
        """
        Convert income object to dictionary for API responses.
        
        Returns:
            dict: Income data
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "description": self.description,
            "amount": float(self.amount),
            "date_received": self.date_received.isoformat() if self.date_received else None,
            "income_type": self.income_type,
            "source": self.source,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "tax_deducted": float(self.tax_deducted) if self.tax_deducted else 0,
            "is_taxable": self.is_taxable,
            "net_amount": float(self.net_amount),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }