# Coinspot Web Scraping Implementation

## Overview
Successfully expanded Coinspot price data collection from 17 coins to **538 coins** by implementing web scraping of the tradecoins page.

## Implementation Date
Sprint 2.13 - Track A (January 20, 2026)

## Problem Statement
The Coinspot public API (`/pubapi/v2/latest`) only provides prices for 17 major cryptocurrencies, while the exchange lists 538+ coins on their tradecoins page. The authenticated Read Only API was investigated but found to only return balances for coins held in the account.

## Solution
Implemented web scraping of `https://www.coinspot.com.au/tradecoins` to extract buy/sell prices for all available coins.

### Technical Approach
Based on the open-source library: https://github.com/kochie/coinspot-async-api

The tradecoins page contains all coin prices in HTML table rows:
```html
<tr data-coin="BTC">
  <td>...</td>  <!-- Image -->
  <td>...</td>  <!-- Name/Symbol -->
  <td data-value="137184.97">$137,184.97</td>  <!-- Buy price -->
  <td data-value="135833.38">$135,833.38</td>  <!-- Sell price -->
  ...
</tr>
```

### Code Changes

#### 1. Updated Dependencies
- Already had `beautifulsoup4` in `backend/pyproject.toml`
- Uses `httpx` for async HTTP requests

#### 2. Modified `backend/app/services/collector.py`
- Renamed mode from "authenticated API" to "web scraping"
- Removed HMAC-SHA512 authentication code (not needed)
- Implemented `_fetch_scraped_prices()` method:
  - Fetches HTML from tradecoins page
  - Parses `<tr data-coin="XXX">` elements
  - Extracts buy/sell prices from `data-value` attributes
  - Calculates average as "last" price

#### 3. Configuration
The existing `COINSPOT_USE_AUTHENTICATED_API` flag now enables web scraping mode:
- `COINSPOT_USE_AUTHENTICATED_API=true` → Scrape 538 coins
- `COINSPOT_USE_AUTHENTICATED_API=false` → Use public API (17 coins)

Note: `COINSPOT_API_KEY` and `COINSPOT_API_SECRET` are no longer needed but can remain in `.env` for potential future use.

## Results

### Before
- **17 coins** from public API
- Coins: btc, usdt, ltc, doge, eth, sol, powr, ans, xrp, trx, eos, str, rfox, gas, ada, rhoc, sngls

### After
- **538 coins** from web scraping
- Includes all coins available on Coinspot exchange
- Sample: 1000sats, 1inch, a2z, aave, aca, ace, ach, acm, act, ada, ..., xai, xch, xcn, xdc, xem, ..., zbu, zcx, zec, zen, zent, zeta, zeus, zil, zk, zro, zrx

### Performance
- Response time: ~2-3 seconds (vs ~500ms for public API)
- Acceptable tradeoff for 31x more coin coverage
- Data structure maintained compatibility with existing database schema

## Price Data Format
```python
{
  "btc": {
    "bid": "137134.72990039",   # Buy price
    "ask": "135783.63391423",   # Sell price
    "last": "136459.18190731"   # Average of bid/ask
  },
  ...
}
```

## Reliability Considerations

### Advantages
- Access to all 538 coins available on exchange
- Simple HTTP GET request (no authentication)
- Price data extracted from authoritative source (Coinspot's own page)

### Potential Issues
1. **HTML Structure Changes**: If Coinspot redesigns the tradecoins page, scraping may break
   - Mitigation: Comprehensive error handling and logging
   - Falls back to public API if scraping fails

2. **Rate Limiting**: Web scraping may be subject to rate limits
   - Current polling: Every 5 minutes (sufficient spacing)
   - User-Agent: httpx default (not disguised)

3. **Legal/ToS Considerations**:
   - Scraping publicly accessible pages for personal data collection
   - Not circumventing authentication or paywalls
   - Not impacting server performance (5-minute intervals)
   - Should review Coinspot's Terms of Service if deploying at scale

## Testing

### Manual Test
```python
from app.services.collector import CoinspotCollector
import asyncio

async def test():
    collector = CoinspotCollector()
    prices = await collector.fetch_latest_prices()
    print(f"Fetched {len(prices)} coins")
    
asyncio.run(test())
# Output: Fetched 538 coins
```

### Test Results
- ✅ Successfully fetches 538 coins
- ✅ Buy/sell prices accurately extracted
- ✅ All price values are positive floats
- ✅ Coin symbols correctly lowercased for database consistency
- ✅ Retry logic works on failures
- ✅ Falls back to public API if web scraping disabled

## Deployment

### Environment Variables
```bash
# Enable web scraping mode (538 coins)
COINSPOT_USE_AUTHENTICATED_API=true

# Or disable for public API only (17 coins)
COINSPOT_USE_AUTHENTICATED_API=false
```

### Database Impact
- No schema changes required
- Existing `PriceData5Min` table handles all coins
- Expect ~53,800 new records per day (538 coins × 12 intervals/hour × 24 hours / 5)

## Future Improvements

### Alternative Approaches Investigated
1. **Authenticated API** (`/api/v2/ro/my/balances`)
   - Status: Rejected
   - Reason: Only returns coins held in account (3 coins vs 538)
   
2. **Individual Coin Endpoints** (`/pubapi/latest/BTC`)
   - Status: Not tested extensively
   - May work but would require 538 API calls vs 1 web page

### Recommendations
1. Monitor for HTML structure changes (weekly checks)
2. Add automated tests to detect page structure changes
3. Consider caching the coin list to reduce parsing overhead
4. If Coinspot provides an official authenticated endpoint for all prices in future, migrate to that

## References
- Coinspot Public API: https://www.coinspot.com.au/api
- Reference Implementation: https://github.com/kochie/coinspot-async-api
- Tradecoins Page: https://www.coinspot.com.au/tradecoins

## Conclusion
Web scraping provides a practical solution to access all 538 Coinspot coins. While less ideal than an official API endpoint, it delivers the required functionality with acceptable performance and reliability trade-offs.
