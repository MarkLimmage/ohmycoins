# mypy: ignore-errors
from decimal import Decimal
from typing import Any


class MACrossoverStrategy:
    def __init__(self, short_window: int = 10, long_window: int = 50, coin_type: str = 'BTC'):
        self.short_window = short_window
        self.long_window = long_window
        self.coin_type = coin_type
        self.prices: list[Decimal] = []

    def generate_signal(self, market_data: dict[str, Any]) -> dict[str, Any]:
        """
        Simple MA Crossover.
        market_data expected to have 'price' and 'coin_type'.
        """
        # If market_data has specific coin info, use it. Otherwise fallback to self.coin_type
        # In a real system, market_data would be a large dict of all coins, so we'd pick ours.
        price_data = market_data.get(self.coin_type)
        raw_price = price_data.get('price')
        if raw_price is None:
             # Fallback if price is explicitly None (e.g. failed fetch)
             raw_price = 1000

        current_price = Decimal(str(raw_price))

        self.prices.append(current_price)

        if len(self.prices) > self.long_window:
            self.prices.pop(0)

        if len(self.prices) < self.long_window:
             # Not enough data
            return {'action': 'hold', 'coin_type': coin_type, 'quantity': Decimal('0'), 'confidence': 0.0}

        # Calculate MAs
        short_ma = sum(self.prices[-self.short_window:]) / self.short_window
        long_ma = sum(self.prices[-self.long_window:]) / self.long_window

        # Simple Logic:
        # If Short MA > Long MA: Bullish -> Buy
        # If Short MA < Long MA: Bearish -> Sell

        # To make it 'trade', we just signal direction.
        # Position management is handled elsewhere (or we assume we want to be long if bullish).

        if short_ma > long_ma:
            # Buy 100 AUD worth
            # Calculate coin quantity
            qty = (Decimal('100') / current_price).quantize(Decimal("0.00000001"))
            return {'action': 'buy', 'coin_type': coin_type, 'quantity': qty, 'confidence': 0.8}
        else:
            return {'action': 'sell', 'coin_type': coin_type, 'quantity': Decimal('0.1'), 'confidence': 0.8} # Sell 0.1 Coin
