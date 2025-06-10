from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import date
from decimal import Decimal

from app.core.database import Base

class Expense(Base):
    """
    Expense model for storing user expense records.
    
    This model represents expense entries for users in the tax management system,
    including various types of tax-deductible business and personal expenses.
    """
    __tablename__ = "expenses"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False, index=True)
    
    # Expense details
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    date_incurred = Column(Date, nullable=False)
    
    # Expense categorization
    expense_type = Column(String(50), nullable=False, index=True)
    # Common expense types: 'office', 'travel', 'equipment', 'marketing', 'professional', 'utilities', 'other'
    
    # Optional fields
    vendor = Column(String(255), nullable=True)  # Supplier/vendor name
    receipt_number = Column(String(100), nullable=True)  # Receipt/invoice number
    notes = Column(Text, nullable=True)
    
    # Tax-related fields
    is_deductible = Column(Boolean, default=True, nullable=False)
    vat_amount = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    business_percentage = Column(Numeric(precision=5, scale=2), default=100, nullable=False)  # For mixed-use expenses
    
    # Timestamps
    created_at = Column(Date, default=date.today, nullable=False)
    updated_at = Column(Date, default=date.today, onupdate=date.today, nullable=False)
    
    # Relationship
    # user = relationship("UserProfile", back_populates="expenses")

    def __repr__(self):
        return f"<Expense(id={self.id}, user_id={self.user_id}, amount={self.amount}, type='{self.expense_type}')>"
    
    def __str__(self):
        return f"{self.description}: R{self.amount:,.2f} ({self.expense_type})"
    
    @property
    def deductible_amount(self) -> Decimal:
        """Calculate the tax-deductible amount based on business percentage."""
        if not self.is_deductible:
            return Decimal('0')
        return self.amount * (self.business_percentage / Decimal('100'))
    
    @property
    def net_amount(self) -> Decimal:
        """Calculate net amount excluding VAT."""
        return self.amount - (self.vat_amount or Decimal('0'))
    
    def to_dict(self) -> dict:
        """
        Convert expense object to dictionary for API responses.
        
        Returns:
            dict: Expense data
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "description": self.description,
            "amount": float(self.amount),
            "date_incurred": self.date_incurred.isoformat() if self.date_incurred else None,
            "expense_type": self.expense_type,
            "vendor": self.vendor,
            "receipt_number": self.receipt_number,
            "notes": self.notes,
            "is_deductible": self.is_deductible,
            "vat_amount": float(self.vat_amount) if self.vat_amount else 0,
            "business_percentage": float(self.business_percentage),
            "deductible_amount": float(self.deductible_amount),
            "net_amount": float(self.net_amount),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }