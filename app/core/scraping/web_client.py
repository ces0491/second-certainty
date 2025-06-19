# app/core/scraping/web_client.py
import logging
from typing import Optional
import httpx
logger = logging.getLogger(__name__)


class SARSWebClient:
    """Client for fetching content from the SARS website."""
    SARS_BASE_URL = "https://www.sars.gov.za"
    TAX_RATES_URL = f"{SARS_BASE_URL}/tax-rates/income-tax/rates-of-tax-for-individuals/"
    ARCHIVE_URL = f"{SARS_BASE_URL}/tax-rates/archive-tax-rates/"

    def __init__(self, timeout: float = 30.0, max_retries: int = 3):
        """
        Initialize the SARS web client.
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.timeout = timeout
        self.max_retries = max_retries

    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from a URL with retries and error handling.
        Args:
            url: The URL to fetch
        Returns:
            The HTML content as a string, or None if the request failed
        """
        logger.info(f"Fetching page: {url}")
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    content_length = len(response.text)
                    logger.info(f"Successfully fetched page: {url} ({content_length} bytes)")
                    return response.text
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP status error fetching {url}: {e.response.status_code} - {e.response.reason_phrase}")
                if attempt == self.max_retries:
                    return None
                logger.info(f"Retrying... (attempt {attempt+1}/{self.max_retries})")
            except httpx.RequestError as e:
                logger.error(f"Request error fetching {url}: {e}")
                if attempt == self.max_retries:
                    return None
                logger.info(f"Retrying... (attempt {attempt+1}/{self.max_retries})")
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None

    async def fetch_current_tax_page(self) -> Optional[str]:
        """Fetch the current tax rates page."""
        return await self.fetch_page(self.TAX_RATES_URL)

    async def fetch_archive_page(self) -> Optional[str]:
        """Fetch the archive tax rates page."""
        return await self.fetch_page(self.ARCHIVE_URL)

    async def fetch_specific_archive_page(self, archive_url: str) -> Optional[str]:
        """
        Fetch a specific archive page.
        Args:
            archive_url: The URL of the archive page to fetch
        Returns:
            The HTML content as a string, or None if the request failed
        """
        # Handle relative URLs
        if not archive_url.startswith("http"):
            archive_url = f"{self.SARS_BASE_URL}{archive_url}"
        return await self.fetch_page(archive_url)
