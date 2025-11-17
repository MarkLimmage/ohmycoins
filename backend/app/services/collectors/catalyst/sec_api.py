"""
SEC EDGAR API collector for regulatory events (Catalyst Ledger).

This collector fetches SEC filings for crypto-related companies to detect
regulatory events that may impact cryptocurrency markets.

Data Source: SEC EDGAR API (https://www.sec.gov/edgar/sec-api-documentation)
Collection Frequency: Daily (filings are published throughout the trading day)
Cost: Free (no authentication required, rate limit: 10 requests/second)

Monitored Companies:
- Coinbase (CIK: 0001679788)
- MicroStrategy (CIK: 0001050446)
- Marathon Digital Holdings (CIK: 0001507605)
- Riot Platforms (CIK: 0001167419)
- Block Inc (formerly Square) (CIK: 0001073349)

Monitored Filing Types:
- Form 4: Insider trading (executives buying/selling)
- Form 8-K: Current events (major announcements)
- Form 10-K: Annual reports
- Form 10-Q: Quarterly reports
- S-1: IPO registrations
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlmodel import Session

from app.models import CatalystEvents
from app.services.collectors.api_collector import APICollector

logger = logging.getLogger(__name__)


class SECAPICollector(APICollector):
    """
    Collector for SEC filings from crypto-related companies.
    
    Collects:
    - Form 4 (Insider Trading)
    - Form 8-K (Current Events)
    - Form 10-K (Annual Reports)
    - Form 10-Q (Quarterly Reports)
    - S-1 (IPO Registrations)
    
    For companies: Coinbase, MicroStrategy, Marathon, Riot, Block
    """
    
    # CIK (Central Index Key) numbers for crypto-related companies
    MONITORED_COMPANIES = {
        "0001679788": "Coinbase",
        "0001050446": "MicroStrategy",
        "0001507605": "Marathon Digital Holdings",
        "0001167419": "Riot Platforms",
        "0001073349": "Block Inc",
    }
    
    # Filing types to monitor with impact scores
    FILING_TYPES = {
        "4": {"name": "Insider Trading", "impact": 5},
        "8-K": {"name": "Current Events", "impact": 8},
        "10-K": {"name": "Annual Report", "impact": 6},
        "10-Q": {"name": "Quarterly Report", "impact": 5},
        "S-1": {"name": "IPO Registration", "impact": 9},
    }
    
    # Map companies to related cryptocurrencies
    COMPANY_CRYPTO_MAP = {
        "Coinbase": ["BTC", "ETH", "USDC"],
        "MicroStrategy": ["BTC"],
        "Marathon Digital Holdings": ["BTC"],
        "Riot Platforms": ["BTC"],
        "Block Inc": ["BTC"],
    }
    
    def __init__(self):
        """Initialize the SEC API collector."""
        super().__init__(
            name="sec_edgar_api",
            ledger="catalyst",
            base_url="https://data.sec.gov",
            timeout=30,
            max_retries=3,
            rate_limit_delay=0.2,  # 5 requests/second = 0.2s between requests
        )
        
        # SEC requires a User-Agent header with contact information
        self.user_agent = "OhMyCoins/1.0 (https://github.com/MarkLimmage/ohmycoins)"
    
    async def collect(self) -> list[dict[str, Any]]:
        """
        Collect recent SEC filings for monitored companies.
        
        Returns:
            List of filing data dictionaries
        
        Raises:
            Exception: If API request fails
        """
        logger.info(
            f"{self.name}: Collecting SEC filings for {len(self.MONITORED_COMPANIES)} companies"
        )
        
        all_filings = []
        
        for cik, company_name in self.MONITORED_COMPANIES.items():
            try:
                # Fetch recent filings for this company
                # SEC EDGAR API endpoint: /submissions/CIK##########.json
                # CIK must be 10 digits with leading zeros
                cik_padded = cik.zfill(10)
                
                headers = {
                    "User-Agent": self.user_agent,
                }
                
                response = await self.fetch_json(
                    f"/submissions/CIK{cik_padded}.json",
                    headers=headers
                )
                
                if not response or "filings" not in response:
                    logger.warning(f"{self.name}: No filings data for {company_name}")
                    continue
                
                # Extract recent filings
                filings_data = response["filings"].get("recent", {})
                
                if not filings_data:
                    logger.warning(f"{self.name}: No recent filings for {company_name}")
                    continue
                
                # Parse filings arrays
                forms = filings_data.get("form", [])
                filing_dates = filings_data.get("filingDate", [])
                accession_numbers = filings_data.get("accessionNumber", [])
                primary_documents = filings_data.get("primaryDocument", [])
                
                # Get filings from the last 30 days
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
                
                for i in range(len(forms)):
                    form_type = forms[i]
                    
                    # Only collect monitored filing types
                    if form_type not in self.FILING_TYPES:
                        continue
                    
                    # Parse filing date
                    filing_date_str = filing_dates[i]
                    try:
                        filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
                        filing_date = filing_date.replace(tzinfo=timezone.utc)
                    except Exception as e:
                        logger.debug(f"{self.name}: Failed to parse date {filing_date_str}: {e}")
                        continue
                    
                    # Skip old filings
                    if filing_date < cutoff_date:
                        continue
                    
                    filing_info = self.FILING_TYPES[form_type]
                    accession_number = accession_numbers[i]
                    primary_doc = primary_documents[i] if i < len(primary_documents) else ""
                    
                    # Build filing URL
                    # Format: https://www.sec.gov/Archives/edgar/data/CIK/ACCESSION/DOCUMENT
                    accession_clean = accession_number.replace("-", "")
                    filing_url = (
                        f"https://www.sec.gov/Archives/edgar/data/{cik}/"
                        f"{accession_clean}/{primary_doc}"
                    )
                    
                    # Get related cryptocurrencies
                    related_cryptos = self.COMPANY_CRYPTO_MAP.get(company_name, [])
                    
                    filing_data = {
                        "event_type": f"sec_filing_{form_type.lower().replace('-', '_')}",
                        "title": f"{company_name} - {filing_info['name']} (Form {form_type})",
                        "description": (
                            f"SEC Form {form_type} filed by {company_name}. "
                            f"Filing date: {filing_date_str}. "
                            f"Accession: {accession_number}"
                        ),
                        "source": "SEC EDGAR",
                        "currencies": related_cryptos if related_cryptos else None,
                        "impact_score": filing_info["impact"],
                        "detected_at": filing_date,
                        "url": filing_url,
                        "collected_at": datetime.now(timezone.utc),
                    }
                    
                    all_filings.append(filing_data)
                    logger.debug(
                        f"{self.name}: Found {form_type} filing for {company_name} "
                        f"on {filing_date_str}"
                    )
                
            except Exception as e:
                logger.error(
                    f"{self.name}: Failed to collect filings for {company_name}: {str(e)}"
                )
                # Continue with other companies
                continue
        
        logger.info(
            f"{self.name}: Collected {len(all_filings)} SEC filings from last 30 days"
        )
        return all_filings
    
    async def validate_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Validate the collected SEC filing data.
        
        Args:
            data: Raw data collected from SEC EDGAR API
        
        Returns:
            Validated data ready for storage
        
        Raises:
            ValueError: If validation fails
        """
        validated = []
        
        for item in data:
            try:
                # Validate required fields
                if not item.get("title"):
                    logger.warning(f"{self.name}: Missing title, skipping")
                    continue
                
                if not item.get("event_type"):
                    logger.warning(f"{self.name}: Missing event_type, skipping")
                    continue
                
                # Validate impact score
                impact_score = item.get("impact_score")
                if impact_score is not None:
                    if not isinstance(impact_score, int) or impact_score < 1 or impact_score > 10:
                        logger.warning(
                            f"{self.name}: Invalid impact score {impact_score}, setting to 5"
                        )
                        item["impact_score"] = 5
                
                validated.append(item)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"{self.name}: Invalid filing data: {str(e)}")
                continue
        
        logger.info(f"{self.name}: Validated {len(validated)}/{len(data)} records")
        return validated
    
    async def store_data(self, data: list[dict[str, Any]], session: Session) -> int:
        """
        Store validated SEC filings in the database.
        
        Args:
            data: Validated data to store
            session: Database session
        
        Returns:
            Number of records stored
        """
        stored_count = 0
        
        for item in data:
            try:
                catalyst_event = CatalystEvents(
                    event_type=item["event_type"],
                    title=item["title"],
                    description=item.get("description"),
                    source=item.get("source"),
                    currencies=item.get("currencies"),
                    impact_score=item.get("impact_score"),
                    detected_at=item.get("detected_at"),
                    url=item.get("url"),
                    collected_at=item["collected_at"],
                )
                
                session.add(catalyst_event)
                stored_count += 1
                
            except Exception as e:
                logger.error(
                    f"{self.name}: Failed to store filing '{item.get('title', 'unknown')[:50]}...': "
                    f"{str(e)}"
                )
                # Continue with other records
                continue
        
        # Commit all records at once
        try:
            session.commit()
            logger.info(f"{self.name}: Stored {stored_count} SEC filing records")
        except Exception as e:
            logger.error(f"{self.name}: Failed to commit records: {str(e)}")
            session.rollback()
            stored_count = 0
        
        return stored_count
