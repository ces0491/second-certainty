# tests/test_core/test_data_scraper.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.data_scraper import SARSDataScraper
from app.core.scraping.sars_service import SARSDataService
from app.core.scraping.web_client import SARSWebClient
from app.core.scraping.tax_parser import TaxDataParser
from app.utils.tax_utils import get_tax_year


class TestSARSDataScraper:
    """Test the main SARSDataScraper facade."""

    @pytest.mark.asyncio
    async def test_update_tax_data_success(self, test_db):
        """Test successful tax data update."""
        mock_result = {
            "tax_year": "2024-2025",
            "brackets": [
                {"lower_limit": 1, "upper_limit": 237100, "rate": 0.18, "base_amount": 0, "tax_year": "2024-2025"}
            ],
            "rebates": {"primary": 17235, "secondary": 9444, "tertiary": 3145, "tax_year": "2024-2025"},
            "thresholds": {"below_65": 95750, "age_65_to_74": 148217, "age_75_plus": 165689, "tax_year": "2024-2025"},
            "medical_credits": {"main_member": 347, "additional_member": 347, "tax_year": "2024-2025"}
        }
        
        with patch('app.core.data_scraper.SARSDataService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_tax_data = AsyncMock(return_value=mock_result)
            mock_service_class.return_value = mock_service
            
            scraper = SARSDataScraper()
            result = await scraper.update_tax_data(test_db, "2024-2025", False)
            
            assert result == mock_result
            mock_service.update_tax_data.assert_called_once_with("2024-2025", False)

    @pytest.mark.asyncio
    async def test_update_tax_data_default_year(self, test_db):
        """Test tax data update with default tax year."""
        current_year = get_tax_year()
        
        with patch('app.core.data_scraper.SARSDataService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_tax_data = AsyncMock(return_value={"tax_year": current_year})
            mock_service_class.return_value = mock_service
            
            scraper = SARSDataScraper()
            await scraper.update_tax_data(test_db)
            
            mock_service.update_tax_data.assert_called_once_with(None, False)

    @pytest.mark.asyncio
    async def test_update_tax_data_force(self, test_db):
        """Test tax data update with force flag."""
        with patch('app.core.data_scraper.SARSDataService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_tax_data = AsyncMock(return_value={"success": True})
            mock_service_class.return_value = mock_service
            
            scraper = SARSDataScraper()
            await scraper.update_tax_data(test_db, "2024-2025", True)
            
            mock_service.update_tax_data.assert_called_once_with("2024-2025", True)

    @pytest.mark.asyncio
    async def test_update_tax_data_exception(self, test_db):
        """Test tax data update when service raises exception."""
        with patch('app.core.data_scraper.SARSDataService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_tax_data = AsyncMock(side_effect=Exception("Service error"))
            mock_service_class.return_value = mock_service
            
            scraper = SARSDataScraper()
            
            with pytest.raises(Exception, match="Service error"):
                await scraper.update_tax_data(test_db, "2024-2025")


class TestSARSWebClient:
    """Test the SARS web client."""

    @pytest.mark.asyncio
    async def test_fetch_page_success(self):
        """Test successful page fetching."""
        mock_html = "<html><body>Test content</body></html>"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = mock_html
            mock_response.raise_for_status = MagicMock()
            
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            client = SARSWebClient()
            result = await client.fetch_page("https://test-url.com")
            
            assert result == mock_html
            mock_client.get.assert_called_once_with("https://test-url.com")

    @pytest.mark.asyncio
    async def test_fetch_page_http_error(self):
        """Test page fetching with HTTP error."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("HTTP 404")
            
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            client = SARSWebClient()
            result = await client.fetch_page("https://test-url.com")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_current_tax_page(self):
        """Test fetching current tax rates page."""
        mock_html = "<html>Tax rates</html>"
        
        with patch.object(SARSWebClient, 'fetch_page', return_value=mock_html) as mock_fetch:
            client = SARSWebClient()
            result = await client.fetch_current_tax_page()
            
            assert result == mock_html
            mock_fetch.assert_called_once_with(client.TAX_RATES_URL)

    @pytest.mark.asyncio
    async def test_fetch_archive_page(self):
        """Test fetching archive tax rates page."""
        mock_html = "<html>Archive</html>"
        
        with patch.object(SARSWebClient, 'fetch_page', return_value=mock_html) as mock_fetch:
            client = SARSWebClient()
            result = await client.fetch_archive_page()
            
            assert result == mock_html
            mock_fetch.assert_called_once_with(client.ARCHIVE_URL)


class TestTaxDataParser:
    """Test the tax data parser."""

    def test_extract_tax_brackets_simple(self):
        """Test extracting tax brackets from simple HTML."""
        html_content = """
        <html>
            <body>
                <table>
                    <tr>
                        <th>Taxable income</th>
                        <th>Rate of tax</th>
                    </tr>
                    <tr>
                        <td>R1 – R237 100</td>
                        <td>18% of taxable income</td>
                    </tr>
                    <tr>
                        <td>R237 101 – R370 500</td>
                        <td>R42 678 + 26% of taxable income above R237 100</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        parser = TaxDataParser()
        brackets = parser.extract_tax_brackets(html_content, "2024-2025")
        
        assert len(brackets) == 2
        
        # First bracket
        assert brackets[0]["lower_limit"] == 1
        assert brackets[0]["upper_limit"] == 237100
        assert brackets[0]["rate"] == 0.18
        assert brackets[0]["base_amount"] == 0
        
        # Second bracket
        assert brackets[1]["lower_limit"] == 237101
        assert brackets[1]["upper_limit"] == 370500
        assert brackets[1]["rate"] == 0.26
        assert brackets[1]["base_amount"] == 42678

    def test_extract_tax_brackets_no_table(self):
        """Test extracting tax brackets when no table exists."""
        html_content = "<html><body><p>No tax table here</p></body></html>"
        
        parser = TaxDataParser()
        brackets = parser.extract_tax_brackets(html_content, "2024-2025")
        
        assert brackets == []

    def test_extract_tax_rebates(self):
        """Test extracting tax rebates from HTML."""
        html_content = """
        <html>
            <body>
                <p>Primary rebate: R 17 235</p>
                <p>Secondary rebate for persons 65 and older: R 9 444</p>
                <p>Tertiary rebate for persons 75 and older: R 3 145</p>
            </body>
        </html>
        """
        
        parser = TaxDataParser()
        rebates = parser.extract_tax_rebates(html_content, "2024-2025")
        
        assert rebates["primary"] == 17235
        assert rebates["secondary"] == 9444
        assert rebates["tertiary"] == 3145
        assert rebates["tax_year"] == "2024-2025"

    def test_extract_tax_thresholds(self):
        """Test extracting tax thresholds from HTML."""
        html_content = """
        <html>
            <body>
                <p>Below 65: R 95 750</p>
                <p>Age 65 to 74: R 148 217</p>
                <p>Age 75 and above: R 165 689</p>
            </body>
        </html>
        """
        
        parser = TaxDataParser()
        thresholds = parser.extract_tax_thresholds(html_content, "2024-2025")
        
        assert thresholds["below_65"] == 95750
        assert thresholds["age_65_to_74"] == 148217
        assert thresholds["age_75_plus"] == 165689
        assert thresholds["tax_year"] == "2024-2025"

    def test_extract_medical_tax_credits(self):
        """Test extracting medical tax credits from HTML."""
        html_content = """
        <html>
            <body>
                <p>Main member: R 347</p>
                <p>Additional member: R 347</p>
            </body>
        </html>
        """
        
        parser = TaxDataParser()
        credits = parser.extract_medical_tax_credits(html_content, "2024-2025")
        
        assert credits["main_member"] == 347
        assert credits["additional_member"] == 347
        assert credits["tax_year"] == "2024-2025"

    def test_find_year_section(self):
        """Test finding year-specific section in HTML."""
        html_content = """
        <html>
            <body>
                <h2>2023 tax year rates</h2>
                <p>Old rates here</p>
                <h2>2024 tax year rates</h2>
                <p>Current rates here</p>
                <h2>Other information</h2>
                <p>Other content</p>
            </body>
        </html>
        """
        
        parser = TaxDataParser()
        section = parser.find_year_section(html_content, "2024-2025")
        
        assert section is not None
        assert "Current rates here" in section
        assert "Old rates here" not in section

    def test_find_archive_link(self):
        """Test finding archive link for specific tax year."""
        html_content = """
        <html>
            <body>
                <a href="/archive/2023-tax-rates">2023 Individual tax rates</a>
                <a href="/archive/2024-tax-rates">2024 Individual tax rates</a>
            </body>
        </html>
        """
        
        parser = TaxDataParser()
        link = parser.find_archive_link(html_content, "2024-2025")
        
        assert link == "/archive/2024-tax-rates"

    def test_find_archive_link_not_found(self):
        """Test finding archive link when year doesn't exist."""
        html_content = """
        <html>
            <body>
                <a href="/archive/2022-tax-rates">2022 Individual tax rates</a>
                <a href="/archive/2023-tax-rates">2023 Individual tax rates</a>
            </body>
        </html>
        """
        
        parser = TaxDataParser()
        link = parser.find_archive_link(html_content, "2024-2025")
        
        assert link is None


class TestSARSDataService:
    """Test the complete SARS data service."""

    @pytest.mark.asyncio
    async def test_update_tax_data_current_page_success(self, test_db):
        """Test successful tax data update from current page."""
        service = SARSDataService(test_db)
        
        mock_html = """
        <html>
            <body>
                <table>
                    <tr><th>Taxable income</th><th>Rate of tax</th></tr>
                    <tr><td>R1 – R237 100</td><td>18% of taxable income</td></tr>
                </table>
                <p>Primary rebate: R 17 235</p>
                <p>Below 65: R 95 750</p>
                <p>Main member: R 347</p>
            </body>
        </html>
        """
        
        with patch.object(service.web_client, 'fetch_current_tax_page', return_value=mock_html), \
             patch.object(service.tax_repository, 'check_tax_data_exists', return_value=False), \
             patch.object(service.tax_repository, 'save_tax_data', return_value=(True, None)):
            
            result = await service.update_tax_data("2024-2025", False)
            
            assert result["tax_year"] == "2024-2025"
            assert len(result["brackets"]) == 1
            assert result["rebates"]["primary"] == 17235

    @pytest.mark.asyncio
    async def test_update_tax_data_existing_data(self, test_db):
        """Test update when data already exists and force is False."""
        service = SARSDataService(test_db)
        
        with patch.object(service.tax_repository, 'check_tax_data_exists', return_value=True):
            
            with pytest.raises(Exception, match="already exists"):
                await service.update_tax_data("2024-2025", False)

    @pytest.mark.asyncio
    async def test_update_tax_data_fallback_to_manual(self, test_db):
        """Test fallback to manual data when all scraping fails."""
        service = SARSDataService(test_db)
        
        with patch.object(service.web_client, 'fetch_current_tax_page', return_value=None), \
             patch.object(service.web_client, 'fetch_archive_page', return_value=None), \
             patch.object(service.tax_repository, 'get_previous_tax_year_data', return_value=None), \
             patch.object(service.tax_repository, 'check_tax_data_exists', return_value=False), \
             patch.object(service.tax_repository, 'save_tax_data', return_value=(True, None)):
            
            result = await service.update_tax_data("2024-2025", False)
            
            # Should use manual data from TaxDataProvider
            assert result["tax_year"] == "2024-2025"
            assert "brackets" in result
            assert len(result["brackets"]) > 0