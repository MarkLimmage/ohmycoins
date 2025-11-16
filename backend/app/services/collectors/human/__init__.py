# human ledger collectors
"""
Human Ledger collectors for social sentiment and narrative data.

Collectors:
- CryptoPanic: Cryptocurrency news with sentiment analysis
"""

from .cryptopanic import CryptoPanicCollector

__all__ = ["CryptoPanicCollector"]
