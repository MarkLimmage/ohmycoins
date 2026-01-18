# human ledger collectors
"""
Human Ledger collectors for social sentiment and narrative data.

Collectors:
- CryptoPanic: Cryptocurrency news with sentiment analysis
- Newscatcher: Aggregated news from 60,000+ sources worldwide
- Reddit: Community discussions and sentiment from crypto subreddits
"""

from .cryptopanic import CryptoPanicCollector
from .newscatcher import NewscatcherCollector
from .reddit import RedditCollector

__all__ = ["CryptoPanicCollector", "NewscatcherCollector", "RedditCollector"]
