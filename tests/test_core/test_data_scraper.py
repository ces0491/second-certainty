# tests/test_core/test_data_scraper
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from app.core.data_scraper import SarsDataScraper
from app.core.scraping.web_client import WebClient

@pytest.mark.asyncio
async def test_web_client_fetch_page():
    """Fixed test with proper async mocking"""
    mock_sars_html = """
    <html>
        <body>
            <h1>Rates of tax for individuals</h1>
            <table>
                <tr>
                    <th>Taxable income</th>
                    <th>Rate of tax</th>
                </tr>
                <tr>
                    <td>R1 – R226 000</td>
                    <td>18% of taxable income</td>
                </tr>
            </table>
        </body>
    </html>
    """
    
    # Create proper async mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.aread = AsyncMock(return_value=mock_sars_html.encode('utf-8'))
    
    # Mock httpx.AsyncClient with context manager support
    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    
    with patch('httpx.AsyncClient', return_value=mock_client_instance):
        web_client = WebClient()
        html = await web_client.fetch_page("https://test-url.com")
        
        assert html == mock_sars_html

@pytest.mark.asyncio
async def test_sars_data_scraper_update_tax_data():
    """Fixed test with proper async service mocking"""
    # Create mock database session
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Mock the service with proper async methods
    mock_service = MagicMock()
    mock_service.update_tax_data = AsyncMock(return_value={
        "success": True,
        "message": "Tax data updated successfully for 2024-2025",
        "data": {
            "tax_brackets": [],
            "rebates": {},
            "thresholds": {}
        },
        "tax_year": "2024-2025"
    })
    
    # Patch the service class
    with patch('app.core.data_scraper.SarsDataService', return_value=mock_service):
        scraper = SarsDataScraper()
        result = await scraper.update_tax_data(mock_db, "2024-2025", False)
        
        assert result["success"] is True
        assert result["tax_year"] == "2024-2025"
        mock_service.update_tax_data.assert_called_once_with("2024-2025", False)
