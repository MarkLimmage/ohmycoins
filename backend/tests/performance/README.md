# Rate Limiting Performance Tests

**Sprint 2.12 - Track B: Performance Testing**

## Overview

This directory contains load tests for validating the rate limiting middleware performance under various conditions.

## Test Suite

### k6 Load Test (`load_test_rate_limiting.js`)

Comprehensive load test that validates:

1. **Per-Minute Rate Limit**: 60 req/min for normal users
2. **Per-Hour Rate Limit**: 1000 req/hour for normal users
3. **Admin Multiplier**: 5x limits (300 req/min, 10000 req/hour)
4. **Concurrent Users**: 100 concurrent users
5. **Redis Performance**: <10ms latency target under 1000 req/min load

## Prerequisites

### 1. Install k6

**macOS:**
```bash
brew install k6
```

**Linux:**
```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D00
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

**Windows:**
```powershell
choco install k6
```

Or download from: https://k6.io/docs/getting-started/installation/

### 2. Set Up Test Environment

1. Start backend services:
   ```bash
   cd /path/to/ohmycoins
   docker compose up -d backend redis db
   ```

2. Create test users:
   ```bash
   # Normal test user
   docker compose exec backend python -c "
   from app.core.db import engine
   from app.models import User
   from sqlmodel import Session, select
   from passlib.context import CryptContext
   
   pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
   
   with Session(engine) as session:
       # Check if user exists
       stmt = select(User).where(User.email == 'test@example.com')
       user = session.exec(stmt).first()
       
       if not user:
           user = User(
               email='test@example.com',
               hashed_password=pwd_context.hash('TestPassword123!'),
               is_superuser=False,
               is_active=True
           )
           session.add(user)
           session.commit()
           print('Test user created')
       else:
           print('Test user already exists')
   "
   
   # Admin test user
   docker compose exec backend python -c "
   from app.core.db import engine
   from app.models import User
   from sqlmodel import Session, select
   from passlib.context import CryptContext
   
   pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
   
   with Session(engine) as session:
       stmt = select(User).where(User.email == 'admin@example.com')
       user = session.exec(stmt).first()
       
       if not user:
           user = User(
               email='admin@example.com',
               hashed_password=pwd_context.hash('AdminPassword123!'),
               is_superuser=True,
               is_active=True
           )
           session.add(user)
           session.commit()
           print('Admin user created')
       else:
           print('Admin user already exists')
   "
   ```

3. Verify rate limiting is enabled:
   ```bash
   docker compose exec backend python -c "
   from app.core.config import settings
   print(f'Rate limiting enabled: {settings.RATE_LIMIT_ENABLED}')
   print(f'Per-minute limit: {settings.RATE_LIMIT_PER_MINUTE}')
   print(f'Per-hour limit: {settings.RATE_LIMIT_PER_HOUR}')
   print(f'Admin multiplier: {settings.RATE_LIMIT_ADMIN_MULTIPLIER}')
   "
   ```

## Running Tests

### Quick Test (2 minutes)
```bash
cd backend/tests/performance
k6 run --duration 2m --vus 10 load_test_rate_limiting.js
```

### Full Test Suite (20 minutes)
```bash
k6 run load_test_rate_limiting.js
```

This runs all 5 scenarios in sequence:
1. Per-minute limit test (2 min)
2. Per-hour limit test (5 min)
3. Admin multiplier test (2 min)
4. Concurrent users test (3 min)
5. Redis performance test (8 min)

### Custom Configuration
```bash
# Test against staging
BASE_URL=https://staging.ohmycoins.example.com k6 run load_test_rate_limiting.js

# Test with different concurrency
k6 run --vus 200 --duration 5m load_test_rate_limiting.js

# Generate HTML report
k6 run --out json=results.json load_test_rate_limiting.js
k6 report results.json --out html=report.html
```

## Success Criteria

### Performance Targets

| Metric | Target | Description |
|--------|--------|-------------|
| Response Time (p95) | <500ms | 95th percentile under 500ms |
| Response Time (p99) | <1000ms | 99th percentile under 1s |
| Redis Latency (p95) | <100ms | Redis operations efficient |
| Redis Latency (optimal) | <10ms | Target for optimal performance |
| Concurrent Users | 100+ | Handle 100+ concurrent users |
| Rate Limit Enforcement | 100% | All limits properly enforced |

### Expected Behavior

1. **Rate Limit Headers**: All responses include:
   - `X-RateLimit-Limit`: Maximum requests allowed
   - `X-RateLimit-Remaining`: Requests remaining in window
   - `X-RateLimit-Reset`: Unix timestamp when limit resets

2. **429 Responses**: When rate limited:
   - Status code: 429 Too Many Requests
   - `Retry-After` header present (seconds until retry allowed)
   - Clear error message

3. **Admin Multiplier**: Admin users have 5x limits:
   - Normal: 60/min, 1000/hour
   - Admin: 300/min, 10000/hour

## Interpreting Results

### Example Output

```
scenarios: (100.00%) 5 scenarios, 150 max VUs, 20m30s max duration
✓ status is 200 or 429
✓ has rate limit headers
✓ has Retry-After header on 429
✓ Redis latency <100ms
✗ Redis latency <10ms

checks.........................: 95.23% ✓ 45812 ✗ 2297
rate_limit_hits................: 2297   19/s
rate_limit_remaining...........: avg=28.45 min=0 max=60
http_req_duration..............: avg=45ms p(95)=120ms p(99)=250ms
http_req_failed................: 4.77%  ✗ 2297 ✓ 45812
```

### Key Metrics

- **checks**: Should be >90% (some 429s expected)
- **rate_limit_hits**: Should be >0 (confirms rate limiting works)
- **http_req_duration p(95)**: Should be <500ms
- **http_req_failed**: Should be <10% (mostly 429s)

### Troubleshooting

**High failure rate (>50%)**:
- Check if backend is running
- Verify test users exist
- Check Redis connectivity

**No rate limit hits**:
- Verify rate limiting is enabled
- Check rate limit configuration
- Ensure Redis is running

**High latency (>1s)**:
- Check Redis performance
- Verify backend resources
- Review concurrent connections

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Performance Tests

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start services
        run: docker compose up -d backend redis db
      
      - name: Wait for services
        run: sleep 30
      
      - name: Create test users
        run: |
          docker compose exec -T backend bash scripts/create_test_users.sh
      
      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D00
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6
      
      - name: Run load tests
        run: |
          cd backend/tests/performance
          k6 run --out json=results.json load_test_rate_limiting.js
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: k6-results
          path: backend/tests/performance/results.json
```

## Monitoring in Production

### CloudWatch Metrics

Monitor these key metrics in production:

```python
# Example CloudWatch metrics to track
metrics = [
    'rate_limit_hits_total',        # Count of 429 responses
    'rate_limit_remaining_gauge',   # Current remaining requests
    'redis_latency_ms',             # Redis operation latency
    'api_request_duration_ms',      # API response time
]
```

### Alarms

Set up CloudWatch alarms for:

1. **High Rate Limit Hit Rate**: >10% of requests get 429
2. **Redis Latency**: p95 >100ms
3. **API Latency**: p95 >500ms

## References

- [k6 Documentation](https://k6.io/docs/)
- [Rate Limiting Middleware](../../app/api/middleware/rate_limiting.py)
- [Sprint 2.11 Track B Report](../../../docs/archive/history/sprints/sprint-2.11/SPRINT_2.11_TRACK_B_COMPLETION.md)
- [OWASP A04: Insecure Design](https://owasp.org/Top10/A04_2021-Insecure_Design/)
- [OWASP A05: Security Misconfiguration](https://owasp.org/Top10/A05_2021-Security_Misconfiguration/)

---

**Last Updated**: 2026-01-18  
**Sprint**: 2.12 Track B  
**Owner**: Developer B (OMC-ML-Scientist)
