import asyncio
import logging
from app.core.collectors.registry import CollectorRegistry
# Import to ensure they are registered (in a real app, this happens via package init or config)
import app.collectors.strategies.news_coindesk
import app.collectors.strategies.news_yahoo
import app.collectors.strategies.news_cryptopanic
import app.collectors.strategies.news_cointelegraph
import app.collectors.strategies.news_decrypt
import app.collectors.strategies.news_cryptoslate
import app.collectors.strategies.news_beincrypto
import app.collectors.strategies.news_newsbtc
import app.collectors.strategies.news_coinmarketcap

async def main():
    logging.basicConfig(level=logging.INFO)
    registry = CollectorRegistry()
    collectors = registry.list_strategies()
    
    print(f"Found {len(collectors)} collectors:")
    for name, metadata in collectors.items():
        # metadata is the class type
        instance = metadata() 
        print(f"- {name}: {instance.description}")
        
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
        print(f"\nMISSING COLLECTORS: {missing}")
        exit(1)
    else:
        print("\nAll expected collectors are registered!")

if __name__ == "__main__":
    asyncio.run(main())
