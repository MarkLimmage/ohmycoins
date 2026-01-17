# BYOM Production Test Suite

**Sprint 2.10 - Track B Phase 2**

## Overview

Comprehensive test suite for the BYOM (Bring Your Own Model) feature, validating end-to-end workflows with OpenAI, Google Gemini, and Anthropic Claude.

## Test Files

### 1. Production Tests
**File:** `tests/services/agent/test_byom_production.py`  
**Lines:** 661  
**Test Classes:** 3  
**Test Functions:** 13

#### Test Classes:
- `TestBYOMProductionWorkflows` - End-to-end agent execution tests
- `TestBYOMPerformanceComparison` - Performance and cost comparison tests  
- `TestBYOMErrorHandling` - Error handling and security tests

#### Coverage:
- ✅ All 3 providers tested with real API invocations
- ✅ System default fallback validation
- ✅ Invalid credential handling
- ✅ Response time comparison
- ✅ Token usage tracking
- ✅ Cost estimation
- ✅ Security isolation tests

### 2. Integration Tests
**File:** `tests/api/routes/test_llm_credentials_integration.py`  
**Lines:** 550  
**Test Classes:** 3  
**Test Functions:** 12

#### Test Classes:
- `TestLLMCredentialsLifecycle` - Complete CRUD operations via API
- `TestCredentialUsageInAgentExecution` - Agent session integration
- `TestCredentialValidation` - Validation workflow tests

#### Coverage:
- ✅ Create, list, update, delete credentials via API
- ✅ Default credential management
- ✅ Duplicate provider prevention
- ✅ Invalid provider rejection
- ✅ Agent session credential usage
- ✅ Security isolation between users

### 3. Performance Benchmark Script
**File:** `scripts/byom_performance_benchmark.py`  
**Lines:** 333  
**Executable:** Yes

#### Features:
- ✅ Automated testing across all 3 providers
- ✅ Multiple prompt complexity levels
- ✅ Response time measurement
- ✅ Token usage tracking
- ✅ Cost estimation with current pricing
- ✅ JSON output for historical tracking
- ✅ Formatted console output

## Running Tests

### Prerequisites

```bash
# Optional: Set API keys for full testing
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIzaSy..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Note:** Tests skip gracefully if API keys are not provided.

### Run All Production Tests

```bash
cd backend
pytest tests/services/agent/test_byom_production.py -v
```

### Run Specific Test Categories

```bash
# End-to-End Workflows
pytest tests/services/agent/test_byom_production.py::TestBYOMProductionWorkflows -v

# Performance Tests (requires API keys)
pytest tests/services/agent/test_byom_production.py::TestBYOMPerformanceComparison -v -m slow

# Error Handling Tests
pytest tests/services/agent/test_byom_production.py::TestBYOMErrorHandling -v
```

### Run Integration Tests

```bash
cd backend
pytest tests/api/routes/test_llm_credentials_integration.py -v
```

### Run Performance Benchmark

```bash
cd backend
python scripts/byom_performance_benchmark.py
```

Output will be saved to `benchmark_results_YYYYMMDD_HHMMSS.json`

## Test Markers

Tests use appropriate pytest markers for selective execution:

| Marker | Description | Usage |
|--------|-------------|-------|
| `@pytest.mark.integration` | Requires database | Standard integration tests |
| `@pytest.mark.requires_api` | Requires real API keys | Skipped in CI without keys |
| `@pytest.mark.slow` | Long-running (>10s) | Performance benchmarks |

### Running Tests by Marker

```bash
# Run only integration tests
pytest -m integration -v

# Skip slow tests
pytest -m "not slow" -v

# Run only tests that don't require API keys
pytest -m "not requires_api" -v
```

## Test Models (Cost-Optimized)

All tests use the cheapest models from each provider:

| Provider | Model | Cost per 1M tokens |
|----------|-------|-------------------|
| OpenAI | gpt-4o-mini | $0.15 input / $0.60 output |
| Google | gemini-1.5-flash | $0.075 input / $0.30 output |
| Anthropic | claude-3-haiku | $0.25 input / $1.25 output |

## Success Criteria

All tests validate:

- ✅ LLM factory creates correct instance types
- ✅ Credentials are properly encrypted/decrypted
- ✅ API keys are masked in responses
- ✅ Invalid credentials are rejected
- ✅ System default fallback works
- ✅ Cross-user access is prevented
- ✅ All 3 providers respond successfully
- ✅ Token usage is tracked accurately
- ✅ Cost estimation matches provider pricing

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run BYOM Tests
  run: |
    cd backend
    pytest tests/services/agent/test_byom_production.py \
      -m "not requires_api" \
      -v
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### With API Keys (Optional)

```yaml
- name: Run BYOM Tests with API Keys
  run: |
    cd backend
    pytest tests/services/agent/test_byom_production.py -v
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## Documentation

Comprehensive test results and analysis documented in:
- `docs/archive/history/sprints/sprint-2.10/TRACK_B_PHASE_2_TESTING_REPORT.md`

Report includes:
- Detailed test results for all scenarios
- Performance comparison data
- Security validation results
- Production deployment recommendations
- Known limitations and future improvements

## Troubleshooting

### Tests Skip with "API key not configured"
**Cause:** Environment variable not set  
**Solution:** Export the required API key or run tests marked `not requires_api`

### Import Errors
**Cause:** Dependencies not installed  
**Solution:** Run `uv sync` or `pip install -e .[dev]`

### Database Connection Errors
**Cause:** PostgreSQL not running  
**Solution:** Start services with `docker-compose up -d db redis`

### Rate Limiting Errors
**Cause:** Too many API requests  
**Solution:** Add delays between tests or use mocking

## Maintenance

### Adding Tests for New Providers

1. Add provider to `COST_PER_1M_TOKENS` in benchmark script
2. Create credential fixture in `test_byom_production.py`
3. Add end-to-end test following existing pattern
4. Update comparison tests to include new provider
5. Update documentation

### Updating Cost Data

Edit `COST_PER_1M_TOKENS` in:
- `scripts/byom_performance_benchmark.py`
- Documentation report

Check provider pricing pages quarterly for updates.

## Contact

For questions or issues with the test suite:
- Review documentation in `TRACK_B_PHASE_2_TESTING_REPORT.md`
- Check existing tests for patterns
- Consult Sprint 2.10 planning documents

---

**Last Updated:** January 2025  
**Test Suite Version:** 1.0  
**Sprint:** 2.10 Track B Phase 2
