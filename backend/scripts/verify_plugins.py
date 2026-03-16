import asyncio
import logging

import app.collectors.strategies.news_beincrypto  # noqa: F401 - side effect import
import app.collectors.strategies.news_coindesk  # noqa: F401 - side effect import
import app.collectors.strategies.news_coinmarketcap  # noqa: F401 - side effect import
import app.collectors.strategies.news_cointelegraph  # noqa: F401 - side effect import
import app.collectors.strategies.news_cryptopanic  # noqa: F401 - side effect import
import app.collectors.strategies.news_cryptoslate  # noqa: F401 - side effect import
import app.collectors.strategies.news_decrypt  # noqa: F401 - side effect import
import app.collectors.strategies.news_newsbtc  # noqa: F401 - side effect import
import app.collectors.strategies.news_yahoo  # noqa: F401 - side effect import

from app.core.collectors.registry import CollectorRegistry  # noqa: I001

async def main():
    logging.basicConfig(level=logging.INFO)
    registry = CollectorRegistry()
    collectors = registry.list_strategies()

    logging.info(f"Found {len(collectors)} collectors:")
    for name, metadata in collectors.items():
        # metadata is the class type
        instance = metadata()
        logging.info(f"- {name}: {instance.description}")

    expected = [
        "news_coindesk",
        "news_yahoo",
        "news_cryptopanic",
        "news_cointelegraph",
        "news_decrypt",
        "news_cryptoslate",
        "news_beincrypto",
        "news_newsbtc",
        "news_coinmarketcap"
    ]

    missing = [name for name in expected if name not in collectors]

    if missing:
        logging.error(f"MISSING COLLECTORS: {missing}")
        exit(1)
    else:
        logging.info("All expected collectors are registered!")

if __name__ == "__main__":
    asyncio.run(main())
