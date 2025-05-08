# app/core/exceptions.py
from fastapi import HTTPException, status

class TaxCalculationError(Exception):
    """Raised when there's an error in tax calculation."""
    pass

class DataScraperError(Exception):
    """Raised when there's an error scraping tax data."""
    pass

class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found."""
    pass

# Convert application exceptions to HTTP exceptions
def exception_handler(request, exc):
    if isinstance(exc, TaxCalculationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    elif isinstance(exc, ResourceNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )
    # Add more exception mappings
    
    # Default case
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred"
    )