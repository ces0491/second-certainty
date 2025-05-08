# tests/test_core/test_data_scraper.py
import pytest
from unittest.mock import patch, MagicMock
import httpx
from app.core.data_scraper import SARSDataScraper

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
async def test_fetch_page(mock_sars_html):
    """Test fetching an HTML page."""
    with patch('httpx.AsyncClient.get') as mock_get:
        # Set up the mock response
        mock_response = MagicMock()
        mock_response.text = mock_sars_html
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        scraper = SARSDataScraper()
        html = await scraper.fetch_page("https://test-url.com")
        
        assert html == mock_sars_html
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_extract_tax_brackets(mock_sars_html):
    """Test extracting tax brackets from HTML."""
    scraper = SARSDataScraper()
    tax_year = "2024-2025"
    
    brackets = await scraper.extract_tax_brackets(mock_sars_html, tax_year)
    
    assert len(brackets) == 3
    assert brackets[0]["lower_limit"] == 1
    assert brackets[0]["upper_limit"] == 226000
    assert brackets[0]["rate"] == 0.18
    assert brackets[0]["base_amount"] == 0
    assert brackets[0]["tax_year"] == tax_year
    
    # Check the highest bracket has upper_limit as None
    assert brackets[2]["lower_limit"] == 353101
    assert brackets[2]["upper_limit"] is None

@pytest.mark.asyncio
async def test_extract_tax_rebates(mock_sars_html):
    """Test extracting tax rebates from HTML."""
    scraper = SARSDataScraper()
    tax_year = "2024-2025"
    
    rebates = await scraper.extract_tax_rebates(mock_sars_html, tax_year)
    
    assert rebates["primary"] == 17235
    assert rebates["secondary"] == 9444
    assert rebates["tertiary"] == 3145
    assert rebates["tax_year"] == tax_year

@pytest.mark.asyncio
async def test_extract_tax_thresholds(mock_sars_html):
    """Test extracting tax thresholds from HTML."""
    scraper = SARSDataScraper()
    tax_year = "2024-2025"
    
    thresholds = await scraper.extract_tax_thresholds(mock_sars_html, tax_year)
    
    assert thresholds["below_65"] == 95750
    assert thresholds["age_65_to_74"] == 148217
    assert thresholds["age_75_plus"] == 165689
    assert thresholds["tax_year"] == tax_year

@pytest.mark.asyncio
async def test_extract_medical_tax_credits(mock_sars_html):
    """Test extracting medical tax credits from HTML."""
    scraper = SARSDataScraper()
    tax_year = "2024-2025"
    
    credits = await scraper.extract_medical_tax_credits(mock_sars_html, tax_year)
    
    assert credits["main_member"] == 347
    assert credits["additional_member"] == 347
    assert credits["tax_year"] == tax_year

@pytest.mark.asyncio
async def test_update_tax_data(mock_sars_html):
    """Test the complete tax data update process."""
    # Create a mock DB session
    mock_db = MagicMock()
    
    with patch.object(SARSDataScraper, 'fetch_page', return_value=mock_sars_html), \
         patch.object(SARSDataScraper, 'get_tax_year', return_value="2024-2025"):
        
        scraper = SARSDataScraper()
        result = await scraper.update_tax_data(mock_db)
        
        # Check if DB operations occurred
        assert mock_db.query.call_count > 0
        assert mock_db.add.call_count > 0
        assert mock_db.commit.called
        
        # Check result structure
        assert "tax_year" in result
        assert "brackets" in result
        assert "rebates" in result
        assert "thresholds" in result
        assert "medical_credits" in result