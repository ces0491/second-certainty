#tests/test_core/test_data_scraper
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
from app.core.data_scraper import SARSDataScraper
from app.core.scraping.web_client import SARSWebClient
from app.core.scraping.tax_parser import TaxDataParser

@pytest.fixture
def mock_sars_html():
    """Return mock HTML content for the SARS tax rates page."""
    return """
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
                <tr>
                    <td>R226 001 – R353 100</td>
                    <td>R40 680 + 26% of taxable income above R226 000</td>
                </tr>
                <tr>
                    <td>R353 101 and above</td>
                    <td>R73 726 + 31% of taxable income above R353 100</td>
                </tr>
            </table>

            <h2>Tax Rebates</h2>
            <p>Primary rebate: R17 235</p>
            <p>Secondary rebate (persons 65 and older): R9 444</p>
            <p>Tertiary rebate (persons 75 and older): R3 145</p>

            <h2>Tax Thresholds</h2>
            <p>Below age 65: R95 750</p>
            <p>Age 65 to 74: R148 217</p>
            <p>Age 75 and over: R165 689</p>

            <h2>Medical Tax Credits</h2>
            <p>Main member: R347</p>
            <p>Additional member: R347</p>
        </body>
    </html>
    """

@pytest.mark.asyncio
async def test_web_client_fetch_page(mock_sars_html):
    """Test the SARSWebClient fetch_page method."""
    with patch('httpx.AsyncClient') as mock_client_class:
        #Set up the mock client and response
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = mock_sars_html
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        web_client = SARSWebClient()
        html = await web_client.fetch_page("https://test-url.com")

        assert html == mock_sars_html
        mock_client.get.assert_called_once_with("https://test-url.com")

def test_tax_parser_extract_tax_brackets(mock_sars_html):
    """Test extracting tax brackets from HTML using TaxDataParser."""
    parser = TaxDataParser()
    tax_year = "2024-2025"

    brackets = parser.extract_tax_brackets(mock_sars_html, tax_year)

    assert len(brackets) >= 1
    #Check that we get some brackets with expected structure
    if brackets:
        bracket = brackets[0]
        assert "lower_limit" in bracket
        assert "rate" in bracket
        assert "tax_year" in bracket
        assert bracket["tax_year"] == tax_year

def test_tax_parser_extract_tax_rebates(mock_sars_html):
    """Test extracting tax rebates from HTML using TaxDataParser."""
    parser = TaxDataParser()
    tax_year = "2024-2025"

    rebates = parser.extract_tax_rebates(mock_sars_html, tax_year)

    assert rebates["primary"] == 17235
    assert rebates["secondary"] == 9444
    assert rebates["tertiary"] == 3145
    assert rebates["tax_year"] == tax_year

def test_tax_parser_extract_tax_thresholds(mock_sars_html):
    """Test extracting tax thresholds from HTML using TaxDataParser."""
    parser = TaxDataParser()
    tax_year = "2024-2025"

    thresholds = parser.extract_tax_thresholds(mock_sars_html, tax_year)

    assert thresholds["below_65"] == 95750
    assert thresholds["age_65_to_74"] == 148217
    assert thresholds["age_75_plus"] == 165689
    assert thresholds["tax_year"] == tax_year

def test_tax_parser_extract_medical_tax_credits(mock_sars_html):
    """Test extracting medical tax credits from HTML using TaxDataParser."""
    parser = TaxDataParser()
    tax_year = "2024-2025"

    credits = parser.extract_medical_tax_credits(mock_sars_html, tax_year)

    assert credits["main_member"] == 347
    assert credits["additional_member"] == 347
    assert credits["tax_year"] == tax_year

@pytest.mark.asyncio
async def test_sars_data_scraper_update_tax_data():
    """Test the SARSDataScraper facade update_tax_data method."""
    #Create a mock database session
    mock_db = MagicMock()

    #Mock the SARSDataService
    with patch('app.core.data_scraper.SARSDataService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        #Mock the update_tax_data method to return some test data
        expected_result = {
            "tax_year": "2024-2025",
            "brackets": [],
            "rebates": {},
            "thresholds": {},
            "medical_credits": {}
        }
        mock_service.update_tax_data.return_value = expected_result

        scraper = SARSDataScraper()
        result = await scraper.update_tax_data(mock_db, "2024-2025", False)

        #Verify the service was called correctly
        mock_service_class.assert_called_once_with(mock_db)
        mock_service.update_tax_data.assert_called_once_with("2024-2025", False)

        #Check result
        assert result == expected_result

@pytest.mark.asyncio
async def test_manual_tax_data_fallback():
    """Test that manual tax data is used when scraping fails."""
    from app.core.scraping.tax_provider import TaxDataProvider

    provider = TaxDataProvider()
    tax_year = "2024-2025"

    data = provider.get_manual_tax_data(tax_year)

    #Verify manual data structure
    assert "tax_year" in data
    assert "brackets" in data
    assert "rebates" in data
    assert "thresholds" in data
    assert "medical_credits" in data
    assert data["tax_year"] == tax_year
    assert len(data["brackets"]) > 0
