# app/core/scraping/tax_parser.py
import logging
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class TaxDataParser:
    """Parser for extracting tax data from SARS website HTML content."""

    def find_year_section(self, html_content: str, tax_year: str) -> Optional[str]:
        """
        Extract section for specific tax year from the page.

        Args:
            html_content: The HTML content to parse
            tax_year: The tax year to find (format: "YYYY-YYYY")

        Returns:
            HTML content for the specific tax year section, or None if not found
        """
        soup = BeautifulSoup(html_content, "html.parser")
        year_end = tax_year.split("-")[1]

        year_patterns = [
            f"{year_end} tax year",  #"2023 tax year"
            f"{year_end}",  #"2022-2023"
            f"tax year {year_end}",  #"tax year 2023"
        ]

        for pattern in year_patterns:
            # Search for headings with this pattern
            year_headings = soup.find_all(["h1", "h2", "h3", "h4"], string=re.compile(pattern, re.IGNORECASE))

            if year_headings:
                logger.info(f"Found heading for year {year_end}: {year_headings[0].text}")

        for heading in year_headings:
            logger.info(f"Found heading for year {year_end}: {heading.text}")

            # Collect all content until next heading of same or higher level
            content = []
            current = heading.next_sibling

            while current and not (current.name in ["h1", "h2", "h3", "h4"] and current.name <= heading.name):
                if current.name:
                    content.append(str(current))
                current = current.next_sibling

            return "".join(content)

        logger.warning(f"Could not find section for tax year {tax_year}")
        return None

    def extract_tax_brackets(self, html_content: str, tax_year: str) -> List[Dict[str, Any]]:
        """
        Extract tax brackets from HTML content.

        Args:
            html_content: The HTML content to parse
            tax_year: The tax year for the data

        Returns:
            List of tax brackets as dictionaries
        """
        soup = BeautifulSoup(html_content, "html.parser")
        tax_brackets = []

        # Find all tables
        all_tables = soup.find_all("table")
        logger.info(f"Found {len(all_tables)} tables on the page")

        for i, table in enumerate(all_tables):
            headers = table.find_all("th")
            header_text = " ".join([h.text.strip() for h in headers])
            logger.info(f"Table {i+1} headers: {header_text}")

            # Check for tax bracket table
            if ("Taxable income" in header_text and "Rate" in header_text) or (
                "Taxable income" in header_text and "tax" in header_text.lower()
            ):
                logger.info(f"Found tax brackets table: Table {i+1}")

                # Extract rows from the table
                rows = table.find_all("tr")[1:]  #Skip header row

                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        # Extract income range and rates
                        income_range = cells[0].text.strip()
                        rate_text = cells[1].text.strip()

                        logger.info(f"Processing row: {income_range} | {rate_text}")

                        # Extract lower and upper bounds
                        income_match = re.search(r"(\d[\d\s]*)\s*[–-]\s*(\d[\d\s]*)", income_range)
                        if income_match:
                            lower_limit = int(income_match.group(1).replace(" ", ""))
                            upper_limit = int(income_match.group(2).replace(" ", ""))
                        else:
                            # Check if it's the highest bracket
                            exceed_match = re.search(r"(\d[\d\s]*)\s*and above", income_range)
                            if exceed_match:
                                lower_limit = int(exceed_match.group(1).replace(" ", ""))
                                upper_limit = None
                            else:
                                logger.warning(f"Could not parse income range: {income_range}")
                                continue

                        # Extract base amount and rate
                        base_amount = 0
                        if "+" in rate_text:
                            base_match = re.search(r"(\d[\d\s]*)", rate_text)
                            if base_match:
                                base_amount = int(base_match.group(1).replace(" ", ""))

                        # Extract rate percentage
                        rate_match = re.search(r"(\d+)%", rate_text)
                        if rate_match:
                            rate = int(rate_match.group(1)) / 100
                        else:
                            # If no percentage, check if it's a flat rate
                            if "18% of taxable income" in rate_text:
                                rate = 0.18
                            else:
                                logger.warning(f"Could not parse tax rate: {rate_text}")
                                continue

                        bracket = {
                            "lower_limit": lower_limit,
                            "upper_limit": upper_limit,
                            "rate": rate,
                            "base_amount": base_amount,
                            "tax_year": tax_year,
                        }

                        logger.info(f"Added tax bracket: {bracket}")
                        tax_brackets.append(bracket)

                # Once we find a valid table, break the loop
                if tax_brackets:
                    break

        if not tax_brackets:
            logger.error(f"No tax brackets found for {tax_year}")

        return tax_brackets

    def extract_tax_rebates(self, html_content: str, tax_year: str) -> Dict[str, Any]:
        """
        Extract tax rebates from HTML content.

        Args:
            html_content: The HTML content to parse
            tax_year: The tax year for the data

        Returns:
            Dictionary containing tax rebate information
        """
        soup = BeautifulSoup(html_content, "html.parser")
        rebates = {"primary": 0, "secondary": 0, "tertiary": 0, "tax_year": tax_year}

        # Get the entire page text to search for rebates
        page_text = soup.get_text()

        # Look for rebate information
        primary_match = re.search(r"[Pp]rimary\s+rebate.*?R\s*([\d\s]+)", page_text)
        if primary_match:
            rebates["primary"] = int(primary_match.group(1).replace(" ", ""))
            logger.info(f"Found primary rebate: R{rebates['primary']}")

        secondary_match = re.search(r"[Ss]econdary\s+rebate.*?R\s*([\d\s]+)", page_text)
        if secondary_match:
            rebates["secondary"] = int(secondary_match.group(1).replace(" ", ""))
            logger.info(f"Found secondary rebate: R{rebates['secondary']}")

        tertiary_match = re.search(r"[Tt]ertiary\s+rebate.*?R\s*([\d\s]+)", page_text)
        if tertiary_match:
            rebates["tertiary"] = int(tertiary_match.group(1).replace(" ", ""))
            logger.info(f"Found tertiary rebate: R{rebates['tertiary']}")

        if rebates["primary"] == 0:
            logger.warning("Primary rebate not found or is zero")

        return rebates

    def extract_tax_thresholds(self, html_content: str, tax_year: str) -> Dict[str, Any]:
        """
        Extract tax thresholds from HTML content.

        Args:
            html_content: The HTML content to parse
            tax_year: The tax year for the data

        Returns:
            Dictionary containing tax threshold information
        """
        soup = BeautifulSoup(html_content, "html.parser")
        thresholds = {"below_65": 0, "age_65_to_74": 0, "age_75_plus": 0, "tax_year": tax_year}

        # Get the entire page text to search for thresholds
        page_text = soup.get_text()

        # Look for threshold information
        below_65_match = re.search(r"[Bb]elow.*?65.*?R\s*([\d\s]+)", page_text)
        if below_65_match:
            thresholds["below_65"] = int(below_65_match.group(1).replace(" ", ""))
            logger.info(f"Found below 65 threshold: R{thresholds['below_65']}")

        age_65_match = re.search(r"[Aa]ge.*?65.*?74.*?R\s*([\d\s]+)", page_text)
        if age_65_match:
            thresholds["age_65_to_74"] = int(age_65_match.group(1).replace(" ", ""))
            logger.info(f"Found age 65-74 threshold: R{thresholds['age_65_to_74']}")

        age_75_match = re.search(r"[Aa]ge.*?75.*?R\s*([\d\s]+)", page_text)
        if age_75_match:
            thresholds["age_75_plus"] = int(age_75_match.group(1).replace(" ", ""))
            logger.info(f"Found age 75+ threshold: R{thresholds['age_75_plus']}")

        if thresholds["below_65"] == 0:
            logger.warning("Below 65 threshold not found or is zero")

        return thresholds

    def extract_medical_tax_credits(self, html_content: str, tax_year: str) -> Dict[str, Any]:
        """
        Extract medical tax credits from HTML content.

        Args:
            html_content: The HTML content to parse
            tax_year: The tax year for the data

        Returns:
            Dictionary containing medical tax credit information
        """
        soup = BeautifulSoup(html_content, "html.parser")
        credits = {"main_member": 0, "additional_member": 0, "tax_year": tax_year}

        # Get the entire page text to search for medical credits
        page_text = soup.get_text()

        # Look for medical credit information
        main_match = re.search(r"[Mm]ain\s+member.*?R\s*([\d\s\.]+)", page_text)
        if main_match:
            credits["main_member"] = float(main_match.group(1).replace(" ", ""))
            logger.info(f"Found main member credit: R{credits['main_member']}")

        additional_match = re.search(r"[Aa]dditional.*?member.*?R\s*([\d\s\.]+)", page_text)
        if additional_match:
            credits["additional_member"] = float(additional_match.group(1).replace(" ", ""))
            logger.info(f"Found additional member credit: R{credits['additional_member']}")

        if credits["main_member"] == 0:
            logger.warning("Main member medical credit not found or is zero")

        return credits

    def find_archive_link(self, archive_html: str, tax_year: str) -> Optional[str]:
        """
        Find the link to a specific tax year archive page.

        Args:
            archive_html: The HTML content of the archive page
            tax_year: The tax year to find

        Returns:
            The URL of the archive page, or None if not found
        """
        soup = BeautifulSoup(archive_html, "html.parser")
        year_end = tax_year.split("-")[1]

        # Find links related to this tax year
        for link in soup.find_all("a"):
            link_text = link.text.strip()
            if year_end in link_text and ("tax rate" in link_text.lower() or "individual" in link_text.lower()):
                archive_link = link.get("hre")
                logger.info(f"Found archive link for {tax_year}: {archive_link}")
                return archive_link

        logger.warning(f"No archive link found for {tax_year}")
        return None

    def check_has_changes(self, section_content: str) -> bool:
        """
        Check if a section mentions 'No changes'.

        Args:
            section_content: The content of the section

        Returns:
            True if the section has changes, False if it mentions 'No changes'
        """
        return not bool(re.search(r"[nN]o changes", section_content))
