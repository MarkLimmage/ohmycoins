# Rate Limiting Documentation

**Sprint 2.12 - Track B: Performance & Security**

## Overview

The Ohmycoins API implements Redis-based rate limiting to prevent abuse and ensure fair resource allocation across all users. Rate limiting is enforced per-user (by user_id) with configurable limits and automatic cleanup.

## Rate Limit Configuration

### Default Limits

| User Type | Per-Minute Limit | Per-Hour Limit |
|-----------|------------------|----------------|
| Normal User | 60 requests | 1000 requests |
| Admin User | 300 requests (5x) | 10000 requests (5x) |

### Configuration

Rate limits are configured via environment variables:

```env
# Rate Limiting Configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_ADMIN_MULTIPLIER=5
```

**Configuration Options:**

- `RATE_LIMIT_ENABLED`: Enable/disable rate limiting (default: `true`)
- `RATE_LIMIT_PER_MINUTE`: Requests per minute for normal users (default: `60`)
- `RATE_LIMIT_PER_HOUR`: Requests per hour for normal users (default: `1000`)
- `RATE_LIMIT_ADMIN_MULTIPLIER`: Multiplier for admin users (default: `5`)

## Rate Limit Headers

All API responses include rate limiting information in the following headers:

### Standard Headers (RFC 6585 Compliant)

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705600320
```

**Header Descriptions:**

| Header | Description | Example |
|--------|-------------|---------|
| `X-RateLimit-Limit` | Maximum requests allowed in current window | `60` |
| `X-RateLimit-Remaining` | Requests remaining in current window | `45` |
| `X-RateLimit-Reset` | Unix timestamp when limit resets | `1705600320` |

### Example Response

**Successful Request (200 OK):**
```http
HTTP/1.1 200 OK
Content-Type: application/json
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705600320

{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com"
}
```

**Rate Limited Request (429 Too Many Requests):**
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705600320
Retry-After: 42

{
  "detail": "Rate limit exceeded. Please try again in 42 seconds."
}
```

## Retry-After Behavior

When a request is rate limited (429 status), the `Retry-After` header indicates how many seconds the client should wait before making another request.

### Client Implementation Examples

**Python (with requests):**
```python
import requests
import time

def make_request_with_retry(url, headers):
    response = requests.get(url, headers=headers)
    
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Rate limited. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return make_request_with_retry(url, headers)  # Retry
    
    return response

# Usage
response = make_request_with_retry(
    'https://api.ohmycoins.com/api/v1/users/me',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)
```

**JavaScript (with fetch):**
```javascript
async function makeRequestWithRetry(url, headers) {
    const response = await fetch(url, { headers });
    
    if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
        console.log(`Rate limited. Waiting ${retryAfter} seconds...`);
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        return makeRequestWithRetry(url, headers);  // Retry
    }
    
    return response;
}

// Usage
const response = await makeRequestWithRetry(
    'https://api.ohmycoins.com/api/v1/users/me',
    { 'Authorization': 'Bearer YOUR_TOKEN' }
);
```

**curl:**
```bash
#!/bin/bash
# Simple retry script for curl

URL="https://api.ohmycoins.com/api/v1/users/me"
TOKEN="YOUR_TOKEN"

while true; do
    RESPONSE=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$URL")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$HTTP_CODE" == "429" ]; then
        RETRY_AFTER=$(echo "$RESPONSE" | grep -i "Retry-After" | cut -d: -f2 | tr -d ' \r')
        echo "Rate limited. Waiting $RETRY_AFTER seconds..."
        sleep "$RETRY_AFTER"
    else
        echo "$BODY"
        break
    fi
done
```

## API Usage Guidelines

### Best Practices

1. **Respect Rate Limits**: Always honor the `Retry-After` header
2. **Cache Responses**: Cache API responses when possible to reduce requests
3. **Batch Operations**: Use batch endpoints instead of multiple single requests
4. **Monitor Headers**: Track `X-RateLimit-Remaining` to avoid hitting limits
5. **Implement Exponential Backoff**: On repeated 429s, increase wait time exponentially

### Example: Monitoring Rate Limits

**Python with logging:**
```python
import requests
import logging

logger = logging.getLogger(__name__)

def check_rate_limit_status(response):
    """Log rate limit status after each request"""
    limit = response.headers.get('X-RateLimit-Limit')
    remaining = response.headers.get('X-RateLimit-Remaining')
    reset = response.headers.get('X-RateLimit-Reset')
    
    if remaining:
        remaining_pct = (int(remaining) / int(limit)) * 100
        logger.info(f"Rate limit: {remaining}/{limit} ({remaining_pct:.1f}% remaining)")
        
        # Warn when approaching limit
        if remaining_pct < 10:
            logger.warning(f"Approaching rate limit! Only {remaining} requests remaining")
    
    return response

# Usage
response = requests.get(url, headers=headers)
check_rate_limit_status(response)
```

### Recommended Request Patterns

**Good Pattern - Respect Limits:**
```python
# Spread requests over time
for item in items:
    response = api.get(f"/items/{item}")
    time.sleep(1)  # Wait 1 second between requests
```

**Bad Pattern - Burst Requests:**
```python
# Don't do this - will hit rate limit immediately
for item in items:
    response = api.get(f"/items/{item}")  # No delay
```

### Rate Limit Strategies

**1. Request Throttling:**
```python
from time import time, sleep

class RateLimitedClient:
    def __init__(self, requests_per_minute=50):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request = 0
    
    def request(self, url, **kwargs):
        # Wait if necessary to respect rate limit
        elapsed = time() - self.last_request
        if elapsed < self.min_interval:
            sleep(self.min_interval - elapsed)
        
        response = requests.get(url, **kwargs)
        self.last_request = time()
        return response
```

**2. Token Bucket:**
```python
from time import time

class TokenBucket:
    def __init__(self, capacity=60, refill_rate=1):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time()
    
    def consume(self, tokens=1):
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        now = time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

# Usage
bucket = TokenBucket(capacity=60, refill_rate=1)  # 60 tokens, 1/sec refill

for item in items:
    while not bucket.consume():
        sleep(0.1)  # Wait for token
    response = api.get(f"/items/{item}")
```

## Admin Users

Admin users (superusers) have a 5x multiplier applied to all rate limits:

| Limit Type | Normal User | Admin User |
|------------|-------------|------------|
| Per-Minute | 60 | 300 |
| Per-Hour | 1000 | 10000 |

**Identifying Admin Status:**
```python
# Admins can check their status
response = requests.get(
    'https://api.ohmycoins.com/api/v1/users/me',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)
user = response.json()
is_admin = user.get('is_superuser', False)

# Check rate limit headers for confirmation
limit = int(response.headers.get('X-RateLimit-Limit'))
if limit == 300:  # Admin per-minute limit
    print("You have admin privileges")
```

## Rate Limiting Architecture

### Implementation Details

**Technology Stack:**
- **Storage**: Redis (atomic operations via INCR)
- **Pattern**: Token bucket with sliding window
- **Granularity**: Per-user (by user_id from JWT token)
- **Windows**: Separate counters for minute and hour limits

**Redis Keys:**
```
rate_limit:{user_id}:minute:{timestamp}
rate_limit:{user_id}:hour:{timestamp}
```

**Key Features:**
1. **Atomic Operations**: Redis INCR ensures thread-safe counting
2. **Automatic Expiry**: Keys expire automatically (TTL)
3. **Distributed**: Works across multiple API servers
4. **Graceful Degradation**: Falls back safely if Redis unavailable

### Performance Characteristics

| Metric | Target | Typical |
|--------|--------|---------|
| Redis Latency (p95) | <10ms | 2-5ms |
| Redis Latency (p99) | <50ms | 8-15ms |
| Middleware Overhead | <5ms | 1-3ms |
| Memory per User | <1KB | ~500 bytes |

### Bypass Prevention

Rate limiting is enforced at the middleware level and cannot be bypassed:

- ✅ **Per user_id**: Multiple tokens for same user share limits
- ✅ **IP-independent**: Changing IP doesn't reset limits
- ✅ **Session-independent**: Logging out/in doesn't reset limits
- ✅ **Token-independent**: Creating new tokens doesn't reset limits

## Troubleshooting

### Common Issues

**1. Unexpected 429 Responses**

**Problem**: Receiving 429 even when not making many requests.

**Possible Causes:**
- Shared account with multiple users/tokens
- Long-running processes making requests
- Third-party integrations consuming quota

**Solution:**
```python
# Check current rate limit status
response = requests.get(url, headers=headers)
print(f"Remaining: {response.headers.get('X-RateLimit-Remaining')}")
print(f"Reset: {response.headers.get('X-RateLimit-Reset')}")

# Calculate time until reset
import time
reset_time = int(response.headers.get('X-RateLimit-Reset'))
wait_seconds = reset_time - int(time.time())
print(f"Wait {wait_seconds} seconds for reset")
```

**2. Rate Limits Not Resetting**

**Problem**: Limits don't seem to reset after the time window.

**Solution:**
- Check server time synchronization (NTP)
- Verify Redis is running and accessible
- Check for clock skew between client and server

**3. High Latency**

**Problem**: Requests are slow due to rate limiting checks.

**Solution:**
- Verify Redis performance (`redis-cli --latency`)
- Check network latency to Redis
- Consider Redis clustering for scale

### Monitoring Rate Limits

**Check Redis Stats:**
```bash
# Connect to Redis
redis-cli

# Count rate limit keys
KEYS rate_limit:*:minute:* | wc -l
KEYS rate_limit:*:hour:* | wc -l

# Check specific user
KEYS rate_limit:123e4567-e89b-12d3-a456-426614174000:*

# View TTL
TTL rate_limit:123e4567-e89b-12d3-a456-426614174000:minute:1705600320

# View current count
GET rate_limit:123e4567-e89b-12d3-a456-426614174000:minute:1705600320
```

**CloudWatch Metrics:**
```python
# Example metrics to track
metrics = {
    'rate_limit_hits_total': 'Count of 429 responses',
    'rate_limit_remaining_avg': 'Average remaining requests',
    'rate_limit_window_resets': 'Count of window resets',
    'redis_latency_ms': 'Redis operation latency',
}
```

## Security Considerations

### OWASP Alignment

Rate limiting addresses the following OWASP Top 10 categories:

**A04:2021 – Insecure Design**
- Prevents abuse through request throttling
- Ensures fair resource allocation
- Mitigates denial-of-service risks

**A05:2021 – Security Misconfiguration**
- Properly configured rate limits
- Clear documentation and defaults
- Monitoring and alerting

### Attack Mitigation

**1. Brute Force Protection**
- Login attempts rate limited
- Account enumeration prevented
- Password reset throttled

**2. API Abuse Prevention**
- Resource exhaustion prevented
- Scraping/harvesting limited
- Cost control for external APIs

**3. DDoS Mitigation**
- Per-user limits prevent single-user floods
- Distributed across Redis (scales horizontally)
- Graceful degradation maintains availability

## Testing

See [Performance Tests README](../backend/tests/performance/README.md) for load testing documentation.

**Quick Test:**
```bash
# Test rate limiting with curl
for i in {1..70}; do
    echo "Request $i:"
    curl -s -w "\nStatus: %{http_code}\n" \
        -H "Authorization: Bearer YOUR_TOKEN" \
        https://api.ohmycoins.com/api/v1/users/me \
        | grep -E "(X-RateLimit|Status|detail)"
    sleep 0.5
done
```

## References

- **RFC 6585**: Additional HTTP Status Codes (429 Too Many Requests)
- **IETF Draft**: RateLimit Header Fields for HTTP
- **OWASP A04:2021**: Insecure Design
- **OWASP A05:2021**: Security Misconfiguration
- **Sprint 2.11 Report**: [Track B Completion](../../docs/archive/history/sprints/sprint-2.11/SPRINT_2.11_TRACK_B_COMPLETION.md)

## Changelog

### Sprint 2.12 (2026-01-18)
- Added comprehensive documentation
- Created load testing suite
- Added client implementation examples
- Documented monitoring and troubleshooting

### Sprint 2.11 (2026-01-18)
- Initial rate limiting implementation
- Redis-based middleware
- Per-user limits with admin multiplier
- Standard rate limit headers

---

**Last Updated**: 2026-01-18  
**Sprint**: 2.12 Track B  
**Owner**: Developer B (OMC-ML-Scientist)  
**Status**: ✅ Complete
