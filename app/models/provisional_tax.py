from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import date
from decimal import Decimal
import enum

from app.core.database import Base

class PaymentStatus(enum.Enum):
    """Enum for provisional tax payment status."""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class ProvisionalTaxPeriod(enum.Enum):
    """Enum for provisional tax periods."""
    FIRST_PERIOD = "first"  # 31 August
    SECOND_PERIOD = "second"  # 28/29 February

class ProvisionalTax(Base):
    """
    Provisional tax model for storing provisional tax payments and estimates.
    
    This model represents provisional tax obligations for users in the 
    South African tax system, tracking estimated income, expenses, and 
    required payments for each tax period.
    """
    __tablename__ = "provisional_taxes"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False, index=True)
    
    # Tax period information
    tax_year = Column(Integer, nullable=False, index=True)  # e.g., 2024 for 2024/2025 tax year
    period = Column(Enum(ProvisionalTaxPeriod), nullable=False)
    due_date = Column(Date, nullable=False)
    
    # Estimated amounts
    estimated_income = Column(Numeric(precision=15, scale=2), nullable=False)
    estimated_expenses = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    estimated_taxable_income = Column(Numeric(precision=15, scale=2), nullable=False)
    estimated_tax = Column(Numeric(precision=15, scale=2), nullable=False)
    
    # Payment information
    payment_amount = Column(Numeric(precision=15, scale=2), nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    payment_date = Column(Date, nullable=True)
    payment_reference = Column(String(100), nullable=True)
    
    # Additional fields
    notes = Column(Text, nullable=True)
    is_calculated = Column(Boolean, default=True, nullable=False)  # Whether system calculated or manual
    penalty_amount = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    interest_amount = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Timestamps
    created_at = Column(Date, default=date.today, nullable=False)
    updated_at = Column(Date, default=date.today, onupdate=date.today, nullable=False)
    
    # Relationship
    # user = relationship("UserProfile", back_populates="provisional_taxes")

    def __repr__(self):
        return f"<ProvisionalTax(id={self.id}, user_id={self.user_id}, year={self.tax_year}, period='{self.period.value}')>"
    
    def __str__(self):
        return f"Provisional Tax {self.tax_year} {self.period.value.title()} Period: R{self.payment_amount:,.2f}"
    
    @property
    def is_overdue(self) -> bool:
        """Check if the provisional tax payment is overdue."""
        return self.due_date < date.today() and self.payment_status == PaymentStatus.PENDING
    
    @property
    def total_amount_due(self) -> Decimal:
        """Calculate total amount due including penalties and interest."""
        return self.payment_amount + (self.penalty_amount or Decimal('0')) + (self.interest_amount or Decimal('0'))
    
    @property
    def effective_tax_rate(self) -> Decimal:
        """Calculate effective tax rate on taxable income."""
        if self.estimated_taxable_income > 0:
            return (self.estimated_tax / self.estimated_taxable_income) * Decimal('100')
        return Decimal('0')
    
    def mark_as_paid(self, payment_date: date = None, reference: str = None):
        """Mark the provisional tax as paid."""
        self.payment_status = PaymentStatus.PAID
        self.payment_date = payment_date or date.today()
        if reference:
            self.payment_reference = reference
    
    def calculate_penalty(self) -> Decimal:
        """Calculate penalty for late payment (simplified calculation)."""
        if not self.is_overdue:
            return Decimal('0')
        
        # Simplified penalty calculation - 10% of outstanding amount
        # In reality, SARS penalty calculation is more complex
        penalty_rate = Decimal('0.10')
        return self.payment_amount * penalty_rate
    
    def to_dict(self) -> dict:
        """
        Convert provisional tax object to dictionary for API responses.
        
        Returns:
            dict: Provisional tax data
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tax_year": self.tax_year,
            "period": self.period.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "estimated_income": float(self.estimated_income),
            "estimated_expenses": float(self.estimated_expenses),
            "estimated_taxable_income": float(self.estimated_taxable_income),
            "estimated_tax": float(self.estimated_tax),
            "payment_amount": float(self.payment_amount),
            "payment_status": self.payment_status.value,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "payment_reference": self.payment_reference,
            "notes": self.notes,
            "is_calculated": self.is_calculated,
            "penalty_amount": float(self.penalty_amount) if self.penalty_amount else 0,
            "interest_amount": float(self.interest_amount) if self.interest_amount else 0,
            "total_amount_due": float(self.total_amount_due),
            "effective_tax_rate": float(self.effective_tax_rate),
            "is_overdue": self.is_overdue,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }