# mypy: ignore-errors
import logging
import random
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.services.trading.base_exchange import BaseExchange

logger = logging.getLogger(__name__)

class OrderBook:
    """
    In-memory OrderBook simulation.
    """
    def __init__(self):
        self.bids: list[tuple[Decimal, Decimal]] = []  # [(price, amount), ...] desc
        self.asks: list[tuple[Decimal, Decimal]] = []  # [(price, amount), ...] asc

    def clear(self):
        self.bids = []
        self.asks = []

    def set_simple_liquidity(self, mid_price: Decimal, spread_percent: Decimal = Decimal('0.001'), depth: int = 10):
        """
        Generates synthetic liquidity around mid_price.
        """
        self.clear()
        half_spread = mid_price * spread_percent / 2

        # Best bid/ask
        best_bid = mid_price - half_spread
        best_ask = mid_price + half_spread

        # Generate levels
        # Simple simulation: linear decay in price, random volume
        for i in range(depth):
            # Bid: price decreases
            bid_p = best_bid * (Decimal('1.0') - (Decimal(i) * Decimal('0.0005')))
            bid_v = Decimal(random.uniform(0.1, 2.0)) # Random volume
            self.bids.append((bid_p, bid_v))

            # Ask: price increases
            ask_p = best_ask * (Decimal('1.0') + (Decimal(i) * Decimal('0.0005')))
            ask_v = Decimal(random.uniform(0.1, 2.0))
            self.asks.append((ask_p, ask_v))

class PaperExchange(BaseExchange):
    """
    Paper Trading Exchange implementation.
    Mimics CoinSpot API but executes simulated trades against local state.
    Stores orders and balances in memory.
    """

    def __init__(self, initial_aud_balance: Decimal = Decimal('100000.0')):
        self.balances: dict[str, Decimal] = {'AUD': initial_aud_balance}
        self.orders: dict[str, dict[str, Any]] = {}
        # self.prices is now derived from orderbooks, but we can keep it as reference or mid-price
        self.prices: dict[str, Decimal] = {}
        self.orderbooks: dict[str, OrderBook] = {}
        self._session = False

        # Default mock price if not set
        self._default_price = Decimal('1000.0')

    def set_price(self, coin_type: str, price: Decimal):
        """
        Sets the market price and generates a synthetic orderbook.
        """
        self.prices[coin_type] = price
        if coin_type not in self.orderbooks:
            self.orderbooks[coin_type] = OrderBook()

        # Generate fresh liquidity
        self.orderbooks[coin_type].set_simple_liquidity(price)
        # Trigger limit order checks here? For now, no.

    def _get_price(self, coin_type: str) -> Decimal:
        return self.prices.get(coin_type, self._default_price)

    def _ensure_liquidity(self, coin_type: str):
        """Ensures there is an orderbook for the coin, even if set_price wasn't called."""
        if coin_type not in self.orderbooks:
            price = self._get_price(coin_type)
            self.set_price(coin_type, price)

    async def __aenter__(self):
        self._session = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._session = False

    async def market_buy(
        self,
        coin_type: str,
        amount_aud: Decimal
    ) -> dict[str, Any]:
        """
        Simulate market buy execution against OrderBook.
        Walks the ASK side.
        """
        logger.info(f"PAPER: Market Buy {amount_aud} AUD of {coin_type}")

        self._ensure_liquidity(coin_type)
        book = self.orderbooks[coin_type]

        current_aud = self.balances.get('AUD', Decimal('0'))
        if current_aud < amount_aud:
            raise ValueError(f"Insufficient funds: {current_aud} < {amount_aud}")

        # Execution Logic
        filled_coin = Decimal('0')
        spent_aud = Decimal('0')
        remaining_aud = amount_aud

        # Walk asks
        # Note: In a real simulation, we consume the orderbook.
        # Here we should probably consume it (remove liquidity).
        # But since we regenerate it constantly, maybe fine.
        # Let's consume it to be realistic.

        fills = []

        while remaining_aud > 0 and book.asks:
            ask_price, ask_vol = book.asks[0]

            cost_of_level = ask_price * ask_vol

            if cost_of_level <= remaining_aud:
                # Fully consume level
                filled_coin += ask_vol
                spent_aud += cost_of_level
                remaining_aud -= cost_of_level
                book.asks.pop(0) # Remove level
                fills.append((ask_price, ask_vol))
            else:
                # Partially consume level
                can_buy_vol = remaining_aud / ask_price
                filled_coin += can_buy_vol
                spent_aud += remaining_aud
                remaining_aud = Decimal('0')
                # Update level
                book.asks[0] = (ask_price, ask_vol - can_buy_vol)
                fills.append((ask_price, can_buy_vol))

        if remaining_aud > 0:
             # Ran out of liquidity? In paper mode, maybe just fill rest at last price or error?
             # For robustness, let's fill at last price with infinite liquidity warning
             logger.warning(f"PAPER: Ran out of liquidity for {coin_type}, filling rest at last price")
             last_price = fills[-1][0] if fills else self._get_price(coin_type)
             rest_vol = remaining_aud / last_price
             filled_coin += rest_vol
             spent_aud += remaining_aud

        # Execute
        self.balances['AUD'] -= spent_aud
        self.balances[coin_type] = self.balances.get(coin_type, Decimal('0')) + filled_coin

        avg_price = spent_aud / filled_coin if filled_coin > 0 else Decimal('0')

        order_id = str(uuid.uuid4())
        order = {
            'id': order_id,
            'status': 'completed',
            'cointype': coin_type,
            'amount': str(filled_coin), # Coins received
            'rate': str(avg_price),
            'total': str(spent_aud),   # AUD spent
            'sold': str(spent_aud),    # AUD sold
            'market': f"{coin_type}/AUD",
            'created': datetime.now(timezone.utc).isoformat(),
            'action': 'buy',
            'type': 'market',
            'fills': [(str(p), str(v)) for p,v in fills] # Debug info
        }
        self.orders[order_id] = order
        return order

    async def market_sell(
        self,
        coin_type: str,
        amount: Decimal
    ) -> dict[str, Any]:
        """
        Simulate market sell execution against OrderBook.
        Walks the BID side.
        """
        logger.info(f"PAPER: Market Sell {amount} {coin_type}")

        self._ensure_liquidity(coin_type)
        book = self.orderbooks[coin_type]

        current_coin = self.balances.get(coin_type, Decimal('0'))
        if current_coin < amount:
            raise ValueError(f"Insufficient {coin_type}: {current_coin} < {amount}")

        filled_aud = Decimal('0')
        remaining_coin = amount
        fills = []

        while remaining_coin > 0 and book.bids:
            bid_price, bid_vol = book.bids[0]

            if bid_vol <= remaining_coin:
                # Fully consume level
                filled_aud += bid_vol * bid_price
                remaining_coin -= bid_vol
                book.bids.pop(0)
                fills.append((bid_price, bid_vol))
            else:
                # Partially consume level
                filled_aud += remaining_coin * bid_price
                # Update level
                book.bids[0] = (bid_price, bid_vol - remaining_coin)
                fills.append((bid_price, remaining_coin))
                remaining_coin = Decimal('0')

        if remaining_coin > 0:
             logger.warning(f"PAPER: Ran out of liquidity for {coin_type}, filling rest at last price")
             last_price = fills[-1][0] if fills else self._get_price(coin_type)
             filled_aud += remaining_coin * last_price
             # remaining_coin consumed

        # Execute
        self.balances[coin_type] -= amount
        self.balances['AUD'] = self.balances.get('AUD', Decimal('0')) + filled_aud

        avg_price = filled_aud / amount if amount > 0 else Decimal('0')

        order_id = str(uuid.uuid4())
        order = {
            'id': order_id,
            'status': 'completed',
            'cointype': coin_type,
            'amount': str(amount),    # Coins sold
            'rate': str(avg_price),
            'total': str(filled_aud), # AUD received
            'sold': str(amount),      # Coins sold
            'market': f"{coin_type}/AUD",
            'created': datetime.now(timezone.utc).isoformat(),
            'action': 'sell',
            'type': 'market',
            'fills': [(str(p), str(v)) for p,v in fills]
        }
        self.orders[order_id] = order
        return order


    async def limit_buy(
        self,
        coin_type: str,
        amount_aud: Decimal,
        rate: Decimal
    ) -> dict[str, Any]:
        """
        Simulate limit buy.
        For simplicity, if price <= limit, fill immediately.
        Otherwise add to open orders.
        """
        logger.info(f"PAPER: Limit Buy {amount_aud} AUD of {coin_type} @ {rate}")

        current_price = self._get_price(coin_type)

        # Check balance immediately (holds funds)
        current_aud = self.balances.get('AUD', Decimal('0'))
        if current_aud < amount_aud:
            raise ValueError(f"Insufficient funds: {current_aud} < {amount_aud}")

        self.balances['AUD'] -= amount_aud

        order_id = str(uuid.uuid4())
        order = {
            'id': order_id,
            'cointype': coin_type,
            'amount': str(amount_aud / rate), # Target coins (approx)
            'rate': str(rate),
            'total': str(amount_aud),
            'market': f"{coin_type}/AUD",
            'created': datetime.now(timezone.utc).isoformat(),
            'action': 'buy',
            'type': 'limit'
        }

        # Check execution
        if current_price <= rate:
            # Executing at limit price (or better? usually limit price)
            # In paper trading, often fill at limit price if crossed
            fill_price = rate
            coin_amount = amount_aud / fill_price

            order['status'] = 'completed'
            order['rate'] = str(fill_price) # Completed rate
            order['amount'] = str(coin_amount)

            self.balances[coin_type] = self.balances.get(coin_type, Decimal('0')) + coin_amount
        else:
            order['status'] = 'open'
            # Funds are held (AUD deducted above)

        self.orders[order_id] = order
        return {'status': 'ok', 'id': order_id}

    async def limit_sell(
        self,
        coin_type: str,
        amount: Decimal,
        rate: Decimal
    ) -> dict[str, Any]:
        """
        Simulate limit sell.
        """
        logger.info(f"PAPER: Limit Sell {amount} {coin_type} @ {rate}")

        current_price = self._get_price(coin_type)

        # Check balance
        current_coin = self.balances.get(coin_type, Decimal('0'))
        if current_coin < amount:
            raise ValueError(f"Insufficient {coin_type}: {current_coin} < {amount}")

        self.balances[coin_type] -= amount

        order_id = str(uuid.uuid4())
        order = {
            'id': order_id,
            'cointype': coin_type,
            'amount': str(amount),
            'rate': str(rate),
            'market': f"{coin_type}/AUD",
            'created': datetime.now(timezone.utc).isoformat(),
            'action': 'sell',
            'type': 'limit'
        }

        if current_price >= rate:
            fill_price = rate
            aud_amount = amount * fill_price

            order['status'] = 'completed'
            order['total'] = str(aud_amount)

            self.balances['AUD'] = self.balances.get('AUD', Decimal('0')) + aud_amount
        else:
            order['status'] = 'open'
            # Coins held

        self.orders[order_id] = order
        return {'status': 'ok', 'id': order_id}

    async def get_orders(
        self,
        coin_type: str | None = None
    ) -> dict[str, Any]:
        """Get open orders"""
        # Filter for open orders
        buy_orders = []
        sell_orders = []

        for o in self.orders.values():
            if o['status'] != 'open':
                continue
            if coin_type and o['cointype'] != coin_type:
                continue

            formatted = o.copy()
            if o['action'] == 'buy':
                buy_orders.append(formatted)
            else:
                sell_orders.append(formatted)

        return {'buyorders': buy_orders, 'sellorders': sell_orders}

    async def get_order_history(
        self,
        coin_type: str | None = None,
        limit: int = 100
    ) -> dict[str, Any]:
        """Get order history (completed/cancelled)"""
        buy_orders = []
        sell_orders = []

        orders_sorted = sorted(self.orders.values(), key=lambda x: x['created'], reverse=True)

        for o in orders_sorted:
            if o['status'] == 'open':
                continue
            if coin_type and o['cointype'] != coin_type:
                continue

            formatted = o.copy()
            if o['action'] == 'buy':
                buy_orders.append(formatted)
            else:
                sell_orders.append(formatted)

            if len(buy_orders) + len(sell_orders) >= limit:
                break

        return {'buyorders': buy_orders, 'sellorders': sell_orders}

    async def cancel_buy_order(self, order_id: str) -> dict[str, Any]:
        if order_id not in self.orders:
             raise ValueError("Order not found")

        order = self.orders[order_id]
        if order['action'] != 'buy' or order['status'] != 'open':
             raise ValueError("Not an open buy order")

        order['status'] = 'cancelled'

        # Refund AUD (amount_aud was deducted)
        # For limit buy, amount is AUD total roughly
        # In limit_buy we did: self.orders[...]['total'] = str(amount_aud)
        refund_aud = Decimal(order['total'])
        self.balances['AUD'] += refund_aud

        return {'status': 'ok'}

    async def cancel_sell_order(self, order_id: str) -> dict[str, Any]:
        if order_id not in self.orders:
             raise ValueError("Order not found")

        order = self.orders[order_id]
        if order['action'] != 'sell' or order['status'] != 'open':
             raise ValueError("Not an open sell order")

        order['status'] = 'cancelled'

        # Refund coins
        refund_coins = Decimal(order['amount'])
        self.balances[order['cointype']] += refund_coins

        return {'status': 'ok'}

    async def get_balances(self) -> dict[str, Any]:
        # transform to api format if needed, typically:
        # { 'balances': [ { 'cointype': 'BTC', 'balance': 0.1 }, ... ] }
        # Check actual coinspot response format.
        # client.py says: Dictionary with balance information for each coin
        # Let's check client.py's docstring or implementation.
        # It just returns request response.

        # Mocking return structure similar to what I expect.
        result = []
        for k, v in self.balances.items():
            result.append({'keys': {'coin': k}, 'balance': float(v)})

        return {'balances': result}

    async def get_balance(self, coin_type: str) -> dict[str, Any]:
        val = self.balances.get(coin_type, Decimal('0'))
        return {'balance': float(val)}
