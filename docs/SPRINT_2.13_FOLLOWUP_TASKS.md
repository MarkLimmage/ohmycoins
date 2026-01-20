# Sprint 2.13 - Follow-up Tasks

## Created: January 20, 2026
## Status: Open

---

## Task 1: Update Unit Tests for Web Scraping Implementation

### Priority: Medium
### Effort: 2-4 hours

### Description
The Coinspot collector unit tests need to be updated to reflect the new web scraping implementation. Currently, 4 unit tests are failing because they mock the old public API approach.

### Failing Tests
- `test_fetch_latest_prices_success`
- `test_fetch_latest_prices_retry_logic`
- `test_collect_and_store_success`
- `test_run_collector_function`

### Required Changes
1. Update mocks to simulate HTML response instead of JSON API response
2. Mock BeautifulSoup parsing behavior
3. Create sample HTML fixtures for testing
4. Update assertions to match new data flow

### Files to Update
- `backend/tests/services/test_collector.py`

### Test Fixtures Needed
```python
MOCK_HTML_RESPONSE = """
<tr data-coin='BTC'>
    <td data-value='45000.00'>$45,000.00</td>
    <td data-value='45100.00'>$45,100.00</td>
</tr>
<tr data-coin='ETH'>
    <td data-value='3000.00'>$3,000.00</td>
    <td data-value='3010.00'>$3,010.00</td>
</tr>
"""
```

### Acceptance Criteria
- All unit tests pass
- Code coverage maintained at >80%
- Both web scraping and public API modes tested
- Error cases properly covered

---

## Task 2: Add Monitoring for HTML Structure Changes

### Priority: Low
### Effort: 1-2 hours

### Description
Create automated monitoring to detect when Coinspot changes their tradecoins page HTML structure, which could break our scraper.

### Suggested Approach
1. Weekly scheduled test that validates HTML structure
2. Alert if expected elements not found
3. Fallback notification to use public API mode

### Implementation
- Add cron job or scheduled task
- Send alert via logging/email if structure changes
- Document in monitoring guide

---

## Task 3: Review Coinspot Terms of Service

### Priority: Low
### Effort: 1 hour

### Description
Review Coinspot's Terms of Service to ensure web scraping is permitted for personal/commercial use at our scale.

### Actions
1. Review current ToS at https://www.coinspot.com.au/terms
2. Document findings
3. Consider reaching out to Coinspot for official API access if needed
4. Document in compliance guide

---

## Task 4: Performance Optimization

### Priority: Low
### Effort: 2-3 hours

### Description
Optimize web scraping performance if needed.

### Potential Improvements
1. Cache coin list (only re-fetch when needed)
2. Parallel processing of price data
3. Reduce parsing overhead
4. Consider compression for storage

### Current Performance
- Response time: 2-3 seconds
- Acceptable for 5-minute polling interval
- No immediate action required

---

_End of Follow-up Tasks_
