# simple_debug.py - Debug script that bypasses config issues
import os
import sys
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Set required environment variables if not present
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite:///./second_certainty.db"
if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "debug-secret-key"

# Now try importing after setting env vars
try:
    from app.core.tax_calculator import TaxCalculator
    from app.models.tax_models import IncomeSource, UserExpense, UserProfile
    from app.utils.tax_utils import calculate_age, get_tax_year
except Exception as e:
    print(f"Import error: {e}")
    print("Trying direct database connection...")

    # Create direct database connection
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./second_certainty.db")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_db_direct():
        return SessionLocal()


def debug_user_profile(user_id: int):
    """Debug user profile and related data with detailed provisional tax info."""
    try:
        # Try to get DB session
        if "get_db_direct" in locals():
            db = get_db_direct()
        else:
            from app.core.config import get_db

            db = next(get_db())

        print(f"🔍 Debugging User Profile for ID {user_id}")
        print("=" * 50)

        # Get user profile
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            print(f"❌ User with ID {user_id} not found")
            return

        print(f"👤 User Details:")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.name} {user.surname}")
        print(f"   Date of Birth: {user.date_of_birth}")
        print(f"   Is Provisional Taxpayer: {user.is_provisional_taxpayer}")
        print(f"   Is Admin: {getattr(user, 'is_admin', False)}")

        # Calculate age
        if user.date_of_birth:
            age = calculate_age(user.date_of_birth)
            print(f"   Current Age: {age}")

        # Get current tax year
        current_tax_year = get_tax_year()
        print(f"\n📅 Current Tax Year: {current_tax_year}")

        # Check income sources
        income_sources = (
            db.query(IncomeSource)
            .filter(IncomeSource.user_id == user_id, IncomeSource.tax_year == current_tax_year)
            .all()
        )

        print(f"\n💰 Income Sources for {current_tax_year}:")
        if income_sources:
            total_income = 0
            for income in income_sources:
                print(f"   - {income.source_type}: R{income.annual_amount:,.2f}")
                print(f"     Description: {income.description or 'N/A'}")
                print(f"     PAYE: {'Yes' if income.is_paye else 'No'}")
                total_income += income.annual_amount
            print(f"   📊 Total Annual Income: R{total_income:,.2f}")
        else:
            print("   ❌ No income sources found")

        # Check expenses
        expenses = (
            db.query(UserExpense).filter(UserExpense.user_id == user_id, UserExpense.tax_year == current_tax_year).all()
        )

        print(f"\n📊 Expenses for {current_tax_year}:")
        if expenses:
            total_expenses = 0
            for expense in expenses:
                print(f"   - {expense.description}: R{expense.amount:,.2f}")
                total_expenses += expense.amount
            print(f"   📊 Total Expenses: R{total_expenses:,.2f}")
        else:
            print("   No expenses found")

        # If user is provisional taxpayer, try tax calculations
        if user.is_provisional_taxpayer and income_sources:
            print(f"\n🧮 Provisional Tax Calculations:")
            try:
                calculator = TaxCalculator(db)

                # Calculate regular tax liability
                tax_result = calculator.calculate_tax_liability(user_id, current_tax_year)
                print(f"   Gross Income: R{tax_result['gross_income']:,.2f}")
                print(f"   Taxable Income: R{tax_result['taxable_income']:,.2f}")
                print(f"   Final Tax: R{tax_result['final_tax']:,.2f}")
                print(f"   Effective Tax Rate: {tax_result['effective_tax_rate']:.2%}")

                # Calculate provisional tax
                prov_tax_result = calculator.calculate_provisional_tax(user_id, current_tax_year)
                print(f"\n📋 Provisional Tax Payments:")
                print(f"   Total Annual Tax: R{prov_tax_result['total_tax']:,.2f}")
                print(
                    f"   First Payment (Due: {prov_tax_result['first_payment']['due_date']}): R{prov_tax_result['first_payment']['amount']:,.2f}"
                )
                print(
                    f"   Second Payment (Due: {prov_tax_result['second_payment']['due_date']}): R{prov_tax_result['second_payment']['amount']:,.2f}"
                )

            except Exception as calc_error:
                print(f"   ❌ Error calculating taxes: {calc_error}")
                import traceback

                traceback.print_exc()
        elif user.is_provisional_taxpayer:
            print(f"\n⚠️  User is marked as provisional taxpayer but has no income sources for {current_tax_year}")
        else:
            print(f"\n💡 User is not a provisional taxpayer")

        # Check all tax years for this user
        print(f"\n📈 All Income Data for User:")
        all_income = db.query(IncomeSource).filter(IncomeSource.user_id == user_id).all()
        if all_income:
            years = set(income.tax_year for income in all_income)
            for year in sorted(years):
                year_income = [inc for inc in all_income if inc.tax_year == year]
                total = sum(inc.annual_amount for inc in year_income)
                print(f"   {year}: R{total:,.2f} ({len(year_income)} source(s))")
        else:
            print("   No income data found for any tax year")

    except Exception as e:
        print(f"❌ Error debugging user profile: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


def list_all_users():
    """List all users to help with debugging."""
    try:
        if "get_db_direct" in locals():
            db = get_db_direct()
        else:
            from app.core.config import get_db

            db = next(get_db())

        users = db.query(UserProfile).all()
        print(f"📋 All Users in Database ({len(users)} total):")
        for user in users:
            prov_status = "✅ Provisional" if user.is_provisional_taxpayer else "❌ Regular"
            admin_status = "👑 Admin" if getattr(user, "is_admin", False) else ""
            print(
                f"   ID: {user.id}, Email: {user.email}, Name: {user.name} {user.surname}, {prov_status} {admin_status}"
            )

    except Exception as e:
        print(f"❌ Error listing users: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_debug.py <user_id>")
        print("   or: python simple_debug.py list")
        sys.exit(1)

    if sys.argv[1] == "list":
        list_all_users()
    else:
        try:
            user_id = int(sys.argv[1])
            debug_user_profile(user_id)
        except ValueError:
            print("Error: User ID must be a number")
            sys.exit(1)
