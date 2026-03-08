"""
SEC EDGAR API collector plugin for regulatory events (Catalyst Ledger).

This collector fetches SEC filings for crypto-related companies to detect
regulatory events that may impact cryptocurrency markets.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.core.config import HTTP_USER_AGENT
from app.models import CatalystEvents

logger = logging.getLogger(__name__)


class CatalystSEC(ICollector):
    """Collector for SEC filings from crypto-related companies."""

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

    @property
    def name(self) -> str:
        return "catalyst_sec"

    @property
    def description(self) -> str:
        return "SEC EDGAR regulatory filings for crypto-related companies"

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "companies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Company CIK numbers to monitor",
                    "default": list(self.MONITORED_COMPANIES.keys()),
                }
            },
            "required": [],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        if "companies" in config:
            if not isinstance(config["companies"], list):
                logger.error("Invalid config: 'companies' must be a list")
                return False
        return True

    async def test_connection(self, config: dict[str, Any]) -> bool:
        """Test connectivity to SEC API."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": HTTP_USER_AGENT}
                # Test with a known CIK
                async with session.get(
                    "https://data.sec.gov/submissions/CIK0001679788.json",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to test SEC connection: {e}")
            return False

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        """Collect recent SEC filings for monitored companies."""
        companies = config.get("companies", list(self.MONITORED_COMPANIES.keys()))
        logger.info(f"Collecting SEC filings for {len(companies)} companies")

        all_filings = []

        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": HTTP_USER_AGENT}

            for cik in companies:
                try:
                    # Pad CIK to 10 digits
                    padded_cik = cik.zfill(10)
                    company_name = self.MONITORED_COMPANIES.get(cik, "Unknown")

                    url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"

                    async with session.get(
                        url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        if resp.status != 200:
                            logger.warning(
                                f"Failed to fetch {company_name}: status {resp.status}"
                            )
                            continue

                        company_data = await resp.json()

                    if not company_data or "filings" not in company_data:
                        logger.warning(f"No filings data for {company_name}")
                        continue

                    # Get the recent filings
                    filings_data = company_data["filings"]
                    if "recent" not in filings_data:
                        logger.warning(f"No recent filings for {company_name}")
                        continue

                    recent_filings = filings_data["recent"]

                    # Iterate through recent filings
                    for _i, filing in enumerate(
                        zip(
                            recent_filings.get("form", []),
                            recent_filings.get("filingDate", []),
                            recent_filings.get("accessionNumber", []),
                            strict=False,
                        )
                    ):
                        try:
                            form_type, filing_date, accession = filing

                            # Only track filing types we care about
                            if form_type not in self.FILING_TYPES:
                                continue

                            # Parse filing date
                            try:
                                filing_datetime = datetime.strptime(
                                    filing_date, "%Y-%m-%d"
                                ).replace(tzinfo=timezone.utc)
                            except Exception:
                                continue

                            # Skip old filings (older than 30 days)
                            if datetime.now(timezone.utc) - filing_datetime > timedelta(
                                days=30
                            ):
                                continue

                            filing_info = self.FILING_TYPES[form_type]
                            currencies = self.COMPANY_CRYPTO_MAP.get(
                                company_name, ["BTC"]
                            )

                            # Create CatalystEvents instance
                            data_point = CatalystEvents(
                                event_type=form_type,
                                title=f"{company_name} {filing_info['name']} (Form {form_type})",
                                description=f"SEC filing: {filing_date}",
                                source="SEC EDGAR",
                                currencies=currencies,
                                impact_score=filing_info["impact"],
                                detected_at=filing_datetime,
                                url=f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form_type}",
                                collected_at=datetime.now(timezone.utc),
                            )

                            all_filings.append(data_point)
                            logger.debug(
                                f"Collected {form_type} filing for {company_name}"
                            )

                        except Exception as e:
                            logger.debug(f"Failed to parse filing: {e}")
                            continue

                    # Wait between requests to respect rate limits
                    await asyncio.sleep(0.2)

                except Exception as e:
                    logger.error(f"Failed to collect filings for {company_name}: {e}")
                    continue

        logger.info(f"Collected {len(all_filings)} SEC filings")
        return all_filings


CollectorRegistry.register(CatalystSEC)
