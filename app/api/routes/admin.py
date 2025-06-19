# app/api/routes/admin.py
import subprocess

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_db
from app.models.tax_models import UserProfile

router = APIRouter()


def run_tax_data_update(force: bool = False, year: str = None):
    """Run the tax data update script as a background task."""
    cmd = ["python", "fetch_tax_data.py"]
    if force:
        cmd.append("--force")
    if year:
        cmd.extend(["--year", year])

    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Log the result
    print(f"Tax data update completed with return code: {result.returncode}")
    if result.stdout:
        print(f"Output: {result.stdout}")
    if result.stderr:
        print(f"Errors: {result.stderr}")


@router.post("/update-tax-data")
async def update_tax_data(
    background_tasks: BackgroundTasks,
    force: bool = False,
    year: str = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Admin endpoint to update tax data from SARS website.

    This endpoint runs the tax data update script in the background
    and returns immediately.
    """
    # Check if user is an admin
    if not hasattr(current_user, "is_admin") or not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can update tax data")

    # Add the task to run in the background
    background_tasks.add_task(run_tax_data_update, force, year)

    return {"message": "Tax data update initiated", "force": force, "year": year if year else "current"}
