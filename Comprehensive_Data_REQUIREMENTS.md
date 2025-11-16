# Comprehensive Data Collection - Requirements Specification

## Document Information

**Version**: 1.0  
**Last Updated**: 2025-11-16  
**Status**: Final  
**Target Size**: 26 KB

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Scope and Objectives](#2-scope-and-objectives)
3. [System Context](#3-system-context)
4. [The 4 Ledgers Framework](#4-the-4-ledgers-framework)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Data Source Requirements](#7-data-source-requirements)
8. [Integration Requirements](#8-integration-requirements)
9. [Security Requirements](#9-security-requirements)
10. [Testing Requirements](#10-testing-requirements)
11. [Success Criteria](#11-success-criteria)
12. [Acceptance Criteria](#12-acceptance-criteria)

---

## 1. Executive Summary

### 1.1 Purpose

This document specifies the complete requirements for upgrading Oh My Coins from basic cryptocurrency price collection to comprehensive market intelligence gathering based on the "4 Ledgers" framework.

### 1.2 Background

**Current Limitation**: Oh My Coins collects only price data, which is a lagging indicator. Prices tell us what happened, not what will happen.

**The Problem**: 
- No predictive power
- Missing market context
- Unable to anticipate moves
- Reactive rather than proactive trading

**The Solution**: Implement the 4 Ledgers framework to collect:
1. **Glass Ledger**: On-chain and fundamental blockchain data
2. **Human Ledger**: Social sentiment and narrative data
3. **Catalyst Ledger**: High-impact event-driven data
4. **Exchange Ledger**: Enhanced market microstructure data

### 1.3 Goals

1. **Predictive Capability**: Provide leading indicators, not just lagging prices
2. **Market Context**: Understand *why* prices move, not just *that* they moved
3. **Event Detection**: Capture high-probability trading opportunities in real-time
4. **Cost Efficiency**: Achieve 80% of premium platform capabilities at <5% of the cost

### 1.4 Success Definition

The system is successful if:
- All 4 ledgers are operational with <1% error rate
- Catalyst events are detected within 1 minute
- System costs remain under $100/month for subscriptions
- Algorithms show measurable improvement using comprehensive data vs. price-only

---

## 2. Scope and Objectives

### 2.1 In Scope

#### Tier 1 (Free - $0/month)
- DeFiLlama API integration for protocol fundamentals
- Glassnode/Santiment dashboard scraping for free on-chain metrics
- SEC API integration for regulatory data
- CoinSpot announcements scraping for listing detection
- CryptoPanic API for tagged crypto news
- Reddit API for retail sentiment
- Enhanced CoinSpot API client for comprehensive market data

#### Tier 2 (Low-Cost - $60/month)
- Nansen Pro API for "smart money" tracking
- Newscatcher API for premium news with sentiment

#### Tier 3 (Complexity Upgrade - $60/month)
- X (Twitter) scraper for influencer sentiment
- Advanced dashboard scrapers for premium metrics

### 2.2 Out of Scope

- Premium API subscriptions over $100/month (Glassnode Studio, Messari Enterprise, etc.)
- Multiple exchange integration (focus remains on CoinSpot only)
- Real-time order book depth analysis (beyond basic bid/ask)
- Custom blockchain node operation
- Alternative data sources (satellite imagery, web traffic, etc.)
- Machine learning model training (data collection only; models are separate phase)

### 2.3 Objectives

#### Primary Objectives
1. **O1**: Implement complete 4 Ledgers data collection framework
2. **O2**: Maintain system subscription costs under $100/month
3. **O3**: Achieve <1 minute latency for catalyst event detection
4. **O4**: Collect minimum 30 days of historical data across all ledgers within first month

#### Secondary Objectives
1. **O5**: Build reusable collector framework for easy source addition
2. **O6**: Implement comprehensive monitoring and alerting
3. **O7**: Create data quality validation pipelines
4. **O8**: Document all data sources and collection methods

---

## 3. System Context

### 3.1 Current System Architecture

```
Oh My Coins (Current State)
├── Backend (FastAPI)
│   ├── User Authentication ✅
│   ├── Coinspot Credentials Management ✅
│   └── Collector Service ✅
│       └── Price Collection (5 min intervals) ✅
├── Database (PostgreSQL)
│   ├── Users ✅
│   ├── Credentials ✅
│   └── price_data_5min ✅ (50,000+ records)
└── Frontend (Planned)
```

### 3.2 Target System Architecture

```
Oh My Coins (Target State)
├── Backend (FastAPI)
│   ├── User Authentication ✅
│   ├── Coinspot Credentials Management ✅
│   └── Comprehensive Data Collection Service 🆕
│       ├── Glass Ledger Collectors 🆕
│       │   ├── DeFiLlama Collector
│       │   ├── Dashboard Scrapers (Glassnode/Santiment)
│       │   └── Nansen Collector (Tier 2)
│       ├── Human Ledger Collectors 🆕
│       │   ├── CryptoPanic Collector
│       │   ├── Newscatcher Collector (Tier 2)
│       │   ├── Reddit Collector
│       │   └── Twitter Scraper (Tier 3)
│       ├── Catalyst Ledger Collectors 🆕
│       │   ├── SEC API Client
│       │   ├── CoinSpot Announcements Scraper
│       │   └── Corporate News Tracker
│       └── Exchange Ledger (Enhanced) 🆕
│           └── CoinSpot Client (Enhanced)
├── Database (PostgreSQL)
│   ├── Users ✅
│   ├── Credentials ✅
│   ├── price_data_5min ✅ (Enhanced)
│   └── New Tables 🆕
│       ├── on_chain_metrics
│       ├── protocol_fundamentals
│       ├── news_sentiment
│       ├── social_sentiment
│       └── catalyst_events
└── Monitoring & Alerts 🆕
    ├── Collector Health Dashboard
    ├── Data Quality Metrics
    └── Event Detection Alerts
```

---

## 4. The 4 Ledgers Framework

### 4.1 Glass Ledger: On-Chain & Fundamental Data

**Definition**: Transparent, immutable blockchain data providing insight into network health, capital flows, and protocol fundamentals.

**Key Characteristics**:
- **Update Frequency**: Daily (most metrics)
- **Latency Tolerance**: High (not time-critical)
- **Signal Strength**: Medium-High
- **Time Horizon**: Medium-term (weeks to months)

**Core Metrics**:
- Active addresses, Transaction count, Network hash rate
- MVRV (Market Value to Realized Value)
- Total Value Locked (TVL), Protocol fees and revenue
- Token holder distribution, Exchange inflows/outflows
- Smart money wallet activity

### 4.2 Human Ledger: Social Sentiment & Narrative

**Definition**: Unstructured human opinion, speculation, and emotional state captured from social platforms, news, and communities.

**Key Characteristics**:
- **Update Frequency**: Real-time to 5 minutes
- **Latency Tolerance**: Low (time-sensitive)
- **Signal Strength**: High (short-term)
- **Time Horizon**: Short-term (minutes to days)

**Core Metrics**:
- News sentiment (bullish/bearish/neutral)
- Social media volume, Influencer sentiment
- Reddit sentiment scores, Trending topics/coins
- Fear & Greed indicators, Search volume trends

### 4.3 Catalyst Ledger: Event-Driven Data

**Definition**: Discrete, high-impact events that trigger immediate and predictable market reactions.

**Key Characteristics**:
- **Update Frequency**: Real-time (sub-minute)
- **Latency Tolerance**: Very Low (seconds matter)
- **Signal Strength**: Very High
- **Time Horizon**: Immediate (seconds to hours)

**Core Events**:
- Exchange listings (CoinSpot Effect)
- Regulatory announcements (SEC, CFTC)
- Institutional adoption (BlackRock, MicroStrategy)
- Network upgrades/hard forks, Security incidents
- Major partnership announcements, ETF approvals/denials

### 4.4 Exchange Ledger: Market Microstructure

**Definition**: Real-time price and execution data from CoinSpot, the sole execution venue.

**Key Characteristics**:
- **Update Frequency**: Real-time (5-10 seconds)
- **Latency Tolerance**: Very Low
- **Signal Strength**: Essential (ground truth)
- **Time Horizon**: Immediate

**Core Data**:
- Latest prices (bid, ask, last), 24h volume
- Price change percentages, Order execution confirmations
- Account balances, Trade history

---

## 5. Functional Requirements

### 5.1 Glass Ledger Requirements

#### FR-GL-001: DeFiLlama Integration
**Priority**: High | **Tier**: 1 (Free)

**Requirements**:
- SHALL integrate with DeFiLlama REST API
- SHALL collect TVL data for configured protocols daily
- SHALL collect protocol fees and revenue data daily
- SHALL support at least 20 protocols (Bitcoin, Ethereum, DeFi protocols)
- SHALL store historical time-series data
- SHALL handle API errors gracefully with retry logic
- SHALL complete collection within 5 minutes
- SHALL cache data to minimize API calls

**Acceptance Test**:
```gherkin
GIVEN the DeFiLlama collector is configured
WHEN daily collection runs
THEN TVL, fees, and revenue data is collected for all configured protocols
AND data is stored in protocol_fundamentals table
AND collection completes within 5 minutes
AND API errors are logged and retried up to 3 times
```

#### FR-GL-002: Dashboard Scraping (Free Metrics)
**Priority**: Medium | **Tier**: 1 (Free)

**Requirements**:
- SHALL scrape free metrics from Glassnode Studio
- SHALL scrape free metrics from Santiment
- SHALL use Playwright for JavaScript rendering
- SHALL collect at minimum: Active Addresses, Transaction Count, MVRV
- SHALL run daily at configured time
- SHALL detect and handle page structure changes
- SHALL implement exponential backoff on failures
- SHOULD rotate user agents to avoid detection

#### FR-GL-003: Nansen Integration (Tier 2)
**Priority**: Medium | **Tier**: 2 ($49/month)

**Requirements**:
- SHALL integrate with Nansen Pro API
- SHALL track "Smart Money" wallet flows for configured tokens
- SHALL query wallet labels on demand
- SHALL update smart money flows every 15 minutes
- SHALL implement credit tracking (pay-as-you-go model)
- SHALL alert when API credits are low
- SHALL provide fallback graceful degradation if API unavailable

### 5.2 Human Ledger Requirements

#### FR-HL-001: CryptoPanic Integration
**Priority**: High | **Tier**: 1 (Free)

**Requirements**:
- SHALL integrate with CryptoPanic free API
- SHALL collect crypto news tagged by sentiment (bullish/bearish/neutral)
- SHALL filter news by configured currencies (BTC, ETH, etc.)
- SHALL update every 5 minutes
- SHALL parse vote counts to calculate sentiment scores
- SHALL deduplicate news articles by URL
- SHALL support both "hot" and "rising" filters

#### FR-HL-002: Newscatcher Integration (Tier 2)
**Priority**: Medium | **Tier**: 2 ($10/month)

**Requirements**:
- SHALL integrate with Newscatcher API
- SHALL search for crypto-related news with configurable keywords
- SHALL collect news with built-in sentiment analysis
- SHALL update every 5 minutes
- SHALL filter by date range (last 1-24 hours)
- SHALL support custom search queries
- SHALL deduplicate with CryptoPanic data

#### FR-HL-003: Reddit Sentiment Collection
**Priority**: Medium | **Tier**: 1 (Free)

**Requirements**:
- SHALL integrate with Reddit API
- SHALL collect posts from r/cryptocurrency and configurable subreddits
- SHALL retrieve "hot" posts (top 50) every 15 minutes
- SHALL extract post title, text, score, upvote ratio, comments count
- SHALL calculate aggregate sentiment score for the community
- SHALL track post flairs for categorization
- SHALL respect Reddit API rate limits (60 requests/minute)

#### FR-HL-004: X (Twitter) Scraping (Tier 3)
**Priority**: Low | **Tier**: 3 (Complexity Upgrade)

**Requirements**:
- SHALL scrape X (Twitter) using Playwright
- SHALL monitor configured list of influencer accounts (30-50 accounts)
- SHALL collect tweets mentioning crypto/coins
- SHALL extract likes, retweets, replies counts
- SHALL update every 5 minutes for tracked accounts
- SHALL implement proxy rotation to avoid blocking
- SHALL mimic human behavior (random delays, scrolling)
- SHALL detect and adapt to anti-bot measures

### 5.3 Catalyst Ledger Requirements

#### FR-CL-001: SEC API Integration
**Priority**: High | **Tier**: 1 (Free)

**Requirements**:
- SHALL integrate with SEC data.sec.gov API
- SHALL monitor filings from configured companies (Coinbase, MicroStrategy, etc.)
- SHALL poll for new filings every 10 minutes during market hours
- SHALL detect crypto-related keywords in filing descriptions
- SHALL retrieve filing metadata (form type, date, accession number)
- SHALL respect SEC rate limit (10 requests/second max)
- SHALL provide User-Agent header as required by SEC

#### FR-CL-002: CoinSpot Announcements Scraping
**Priority**: Critical | **Tier**: 1 (Free)

**Requirements**:
- SHALL scrape CoinSpot Zendesk announcements page
- SHALL poll every 30-60 seconds for new announcements
- SHALL detect listing-related keywords ("support", "listing", "mainnet", "airdrop")
- SHALL extract coin name from announcement title
- SHALL trigger immediate alerts for new listings
- SHALL maintain history of seen announcements to detect new ones
- SHALL complete scrape within 5 seconds
- SHALL implement robust error handling (CoinSpot availability critical)

#### FR-CL-003: Corporate News Tracking
**Priority**: Medium | **Tier**: 1 (Free)

**Requirements**:
- SHALL track Bitcoin/Ethereum corporate treasuries using CoinGecko API
- SHALL monitor for treasury additions/changes
- SHALL scrape The Block's Bitcoin Treasuries page as backup
- SHALL detect major institutional announcements (ETFs, adoptions)
- SHALL cross-reference with Newscatcher news (if available)
- SHALL update daily for treasury data
- SHALL provide real-time alerts for major announcements

### 5.4 Exchange Ledger Requirements

#### FR-EL-001: Enhanced CoinSpot Integration
**Priority**: Critical | **Tier**: 1 (Free)

**Requirements**:
- SHALL enhance existing CoinSpot API client
- SHALL collect latest prices for all coins every 5-10 seconds
- SHALL store bid, ask, last prices (if available from API)
- SHALL collect 24h volume data
- SHALL maintain existing trade execution capabilities
- SHALL implement nonce management for authentication
- SHALL generate HMAC-SHA512 signatures correctly
- SHALL handle rate limits (1000 requests/minute)
- SHALL provide real-time price updates to algorithms

#### FR-EL-002: Order Execution (Existing + Validation)
**Priority**: Critical | **Tier**: 1 (Free)

**Requirements**:
- SHALL support market buy orders
- SHALL support market sell orders
- SHALL validate sufficient balance before orders
- SHALL use 0.1% fee tier (market orders) not 1% (instant orders)
- SHALL return order confirmation with execution price
- SHALL log all orders for audit trail
- SHALL implement order retry logic for transient failures

---

## 6. Non-Functional Requirements

### 6.1 Performance Requirements

#### NFR-P-001: Collection Latency

| Ledger | Target Latency | Maximum Acceptable Latency |
|--------|----------------|---------------------------|
| Catalyst | < 30 seconds | 1 minute |
| Human | < 5 minutes | 10 minutes |
| Exchange | < 10 seconds | 30 seconds |
| Glass | < 24 hours | 48 hours |

#### NFR-P-002: System Throughput
- SHALL support 100+ concurrent data collection tasks
- SHALL process 10,000+ data points per hour across all ledgers
- SHALL handle price updates for 500+ coins simultaneously

#### NFR-P-003: Database Performance
- SHALL complete price data queries (24h range) within 1 second
- SHALL support 100 concurrent database connections
- SHALL maintain query performance as data grows to 1M+ records

### 6.2 Reliability Requirements

#### NFR-R-001: Uptime
- SHALL maintain 99% uptime for critical collectors (Catalyst, Exchange)
- SHALL maintain 95% uptime for non-critical collectors (Glass, Human)

#### NFR-R-002: Data Collection Success Rate
- SHALL achieve 99% success rate for API-based collection
- SHALL achieve 90% success rate for web scraping-based collection

#### NFR-R-003: Fault Tolerance
- SHALL continue operating if individual collectors fail
- SHALL provide graceful degradation (e.g., use cached data)
- SHALL automatically retry failed collections with exponential backoff
- SHALL alert on repeated failures (3+ consecutive failures)

### 6.3 Scalability Requirements

#### NFR-S-001: Horizontal Scalability
- SHALL support running multiple collector instances in parallel
- SHALL use locking mechanism to prevent duplicate collections
- SHALL support distributed deployment across multiple servers

#### NFR-S-002: Data Growth
- SHALL support 1GB+ data growth per month
- SHALL implement data retention policies (e.g., aggregate old data)
- SHALL maintain performance as data grows to 100GB+

### 6.4 Maintainability Requirements

#### NFR-M-001: Code Quality
- SHALL maintain 80%+ test coverage
- SHALL pass all linting checks (ruff)
- SHALL pass type checking (mypy)
- SHALL follow existing code style and conventions

#### NFR-M-002: Documentation
- SHALL document all collector APIs and configuration
- SHALL provide runbook for common failure scenarios
- SHALL maintain updated architecture diagrams
- SHALL document data schema and relationships

#### NFR-M-003: Monitoring
- SHALL provide health check endpoints for all collectors
- SHALL expose Prometheus-compatible metrics
- SHALL log all collection attempts with outcomes
- SHALL provide dashboards for data quality monitoring

---

## 7. Data Source Requirements

### 7.1 Free Data Sources (Tier 1)

| Source | Endpoint | Rate Limit | Cost | Update Freq |
|--------|----------|------------|------|-------------|
| DeFiLlama | api.llama.fi | Reasonable | $0 | Daily |
| SEC API | data.sec.gov | 10 req/sec | $0 | 10 min |
| CryptoPanic | cryptopanic.com/api | Reasonable | $0 | 5 min |
| Reddit API | oauth.reddit.com | 60 req/min | $0 | 15 min |
| CoinSpot API | coinspot.com.au | 1000 req/min | $0 | 5-10 sec |
| CoinGecko | api.coingecko.com | 10-50/min | $0 | Daily |

### 7.2 Low-Cost Data Sources (Tier 2)

| Source | Cost | Rate Limit | Data Type | Update Freq |
|--------|------|------------|-----------|-------------|
| Nansen Pro | $49/mo | Pay-as-you-go credits | Smart money flows | 15 min |
| Newscatcher | $10/mo | 1000 req/month (Basic) | News + sentiment | 5 min |

### 7.3 Web Scraping Targets (Tier 1 & 3)

| Target | Method | Complexity | Maintenance | Update Freq |
|--------|--------|------------|-------------|-------------|
| Glassnode Studio | Playwright | Very High | High | Daily |
| Santiment | Playwright | Very High | High | Daily |
| CoinSpot Announcements | BeautifulSoup | Low-Medium | Low | 30-60 sec |
| X (Twitter) | Playwright + Proxies | Very High | Very High | 5 min |

---

## 8. Integration Requirements

### 8.1 Database Integration

#### IR-DB-001: Schema Design
- SHALL design normalized schema for all 4 ledgers
- SHALL use appropriate indexes for query performance
- SHALL implement time-series patterns for historical data
- SHALL use JSONB for flexible metadata storage where appropriate

#### IR-DB-002: Data Retention
- SHALL retain raw data for minimum 90 days
- SHALL aggregate data older than 90 days to daily summaries
- SHALL provide configurable retention policies per data type
- SHALL implement automated cleanup jobs

### 8.2 API Integration

#### IR-API-001: REST API Clients
- SHALL implement reusable HTTP client with retry logic
- SHALL handle rate limiting with exponential backoff
- SHALL support circuit breaker pattern for failing APIs
- SHALL log all API requests/responses for debugging

#### IR-API-002: Authentication Management
- SHALL securely store API keys (encrypted at rest)
- SHALL support API key rotation without service restart
- SHALL implement key validation on startup
- SHALL alert on authentication failures

### 8.3 Scheduler Integration

#### IR-SCH-001: Collection Scheduling
- SHALL use APScheduler (existing) for collection orchestration
- SHALL support cron-style schedules (e.g., "every 5 minutes")
- SHALL provide manual trigger capability for each collector
- SHALL implement schedule conflict detection

#### IR-SCH-002: Priority Management
- SHALL prioritize Catalyst > Human > Exchange > Glass
- SHALL implement queue for collection tasks
- SHALL support urgent task interruption (e.g., listing detected)

### 8.4 Monitoring Integration

#### IR-MON-001: Health Checks
- SHALL expose /health endpoint reporting collector status
- SHALL implement per-collector health status
- SHALL provide last successful collection timestamp
- SHALL report error counts and rates

#### IR-MON-002: Alerting
- SHALL integrate with existing monitoring system
- SHALL alert on collector failures (3+ consecutive)
- SHALL alert on data quality issues (anomalies, gaps)
- SHALL alert on rate limit warnings
- SHALL alert on API credit depletion (for paid services)

---

## 9. Security Requirements

### 9.1 API Security

#### SR-API-001: Credential Storage
- SHALL encrypt all API keys at rest using AES-256
- SHALL NOT log API keys or secrets
- SHALL use environment variables for credentials
- SHALL implement key rotation procedures

#### SR-API-002: Network Security
- SHALL use HTTPS for all external API calls
- SHALL validate SSL certificates
- SHALL implement timeout for all network requests
- SHALL use connection pooling with limits

### 9.2 Web Scraping Security

#### SR-WS-001: Anti-Bot Compliance
- SHALL respect robots.txt where applicable
- SHALL implement rate limiting to avoid overload
- SHALL use reasonable user agents
- SHALL NOT use techniques that violate terms of service

#### SR-WS-002: Proxy Management (Tier 3)
- SHALL use reputable proxy services
- SHALL rotate proxies to distribute load
- SHALL validate proxy anonymity
- SHALL monitor proxy performance and ban rate

### 9.3 Data Security

#### SR-DS-001: Data Integrity
- SHALL validate all collected data before storage
- SHALL detect and handle data anomalies
- SHALL implement checksums for critical data
- SHALL provide audit trail for data changes

#### SR-DS-002: Data Privacy
- SHALL NOT collect personally identifiable information
- SHALL anonymize wallet addresses if required
- SHALL comply with data protection regulations
- SHALL provide data deletion capabilities

---

## 10. Testing Requirements

### 10.1 Unit Testing

#### TR-UT-001: Collector Tests
- SHALL test each collector in isolation
- SHALL mock external API/scraping calls
- SHALL achieve 80%+ code coverage
- SHALL test error handling paths
- SHALL test rate limiting logic

### 10.2 Integration Testing

#### TR-IT-001: End-to-End Tests
- SHALL test full collection pipeline (source → DB)
- SHALL test scheduler integration
- SHALL test error recovery
- SHALL test failover scenarios

### 10.3 Performance Testing

#### TR-PT-001: Load Testing
- SHALL test system under expected load (100+ concurrent collections)
- SHALL test database performance with 1M+ records
- SHALL identify bottlenecks and optimize

### 10.4 Security Testing

#### TR-ST-001: Vulnerability Testing
- SHALL scan for OWASP Top 10 vulnerabilities
- SHALL test authentication bypass attempts
- SHALL test injection attacks
- SHALL validate encryption implementation

---

## 11. Success Criteria

### 11.1 Technical Success Metrics

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Catalyst Latency | < 30 seconds | < 1 minute |
| Human Latency | < 5 minutes | < 10 minutes |
| Glass Latency | < 24 hours | < 48 hours |
| Exchange Latency | < 10 seconds | < 30 seconds |
| Collection Success Rate (API) | > 99% | > 95% |
| Collection Success Rate (Scraping) | > 90% | > 80% |
| System Uptime (Critical) | > 99% | > 95% |
| System Uptime (Non-Critical) | > 95% | > 90% |
| Data Error Rate | < 1% | < 5% |
| Test Coverage | > 80% | > 70% |

### 11.2 Business Success Metrics

| Metric | Target | Measurement Period |
|--------|--------|-------------------|
| Subscription Cost | < $100/month | Ongoing |
| Catalyst Events Detected | > 3 CoinSpot listings | First 30 days |
| Algorithm Performance Improvement | Measurable gain vs. price-only | First 60 days |
| ROI Achievement | System "pays for itself" | Within 6 months |
| Data Coverage | All 4 ledgers operational | Within 30 days |

---

## 12. Acceptance Criteria

### 12.1 Tier 1 Acceptance (Free Sources)

**Definition of Done**:
- [ ] All Tier 1 collectors implemented and tested
- [ ] Glass Ledger: DeFiLlama API collecting daily for 20+ protocols
- [ ] Glass Ledger: Dashboard scrapers collecting daily on-chain metrics
- [ ] Human Ledger: CryptoPanic API collecting every 5 minutes
- [ ] Human Ledger: Reddit API collecting every 15 minutes
- [ ] Catalyst Ledger: SEC API polling every 10 minutes
- [ ] Catalyst Ledger: CoinSpot announcements scraper running every 30 seconds
- [ ] Exchange Ledger: Enhanced CoinSpot client collecting every 10 seconds
- [ ] All data stored in appropriate database tables
- [ ] Health check endpoint operational
- [ ] Monitoring dashboards deployed
- [ ] Alert system operational
- [ ] Documentation complete (API docs, runbook)
- [ ] Test coverage > 80%
- [ ] All tests passing
- [ ] 30 days of historical data collected across all ledgers
- [ ] Zero critical security vulnerabilities
- [ ] Subscription cost = $0/month (infrastructure only)

**Validation**:
- Technical review by lead developer
- Data quality audit (spot check 100 random data points)
- Stress test (24 hours continuous operation)
- Listing detection test (manual trigger + verification < 1 minute)

---

### 12.2 Tier 2 Acceptance (Low-Cost Upgrade)

**Definition of Done**:
- [ ] All Tier 1 acceptance criteria met
- [ ] Nansen Pro API integrated and collecting every 15 minutes
- [ ] Newscatcher API integrated and collecting every 5 minutes
- [ ] Smart money flow data available for 10+ tracked tokens
- [ ] Premium news sentiment improving algorithm inputs
- [ ] API credit monitoring operational for Nansen
- [ ] Subscription cost < $60/month
- [ ] 30 days of Tier 2 data collected
- [ ] Measurable algorithm improvement vs. Tier 1 only

**Validation**:
- Side-by-side comparison: Tier 1 data vs. Tier 1+2 data in algorithm performance
- Cost verification (actual bills < $60/month)
- Reliability check (Tier 2 sources maintain 99% uptime)

---

### 12.3 Tier 3 Acceptance (Complexity Upgrade)

**Definition of Done**:
- [ ] All Tier 1 and Tier 2 acceptance criteria met
- [ ] X (Twitter) scraper operational for 30 influencer accounts
- [ ] Advanced dashboard scrapers extracting premium metrics
- [ ] Sentiment pipeline processing influencer tweets
- [ ] Proxy rotation working without detection
- [ ] Scraper maintenance runbook documented
- [ ] Subscription cost remains < $60/month (proxies counted as infrastructure)
- [ ] Influencer sentiment data improving algorithm signal
- [ ] 30 days of Tier 3 data collected

**Validation**:
- Scraper reliability test (7 days continuous operation with <10% failure rate)
- Sentiment quality audit (manual review of 100 classified tweets)
- Anti-bot detection test (verify no account bans or blocks)
- Algorithm improvement measurement

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Alpha** | Excess returns above market benchmarks; predictive edge |
| **Catalyst Event** | High-impact event triggering immediate market reaction |
| **Glass Ledger** | On-chain and fundamental blockchain data |
| **Human Ledger** | Social sentiment and narrative data |
| **Catalyst Ledger** | Event-driven market-moving data |
| **Exchange Ledger** | Market microstructure and execution data |
| **MVRV** | Market Value to Realized Value ratio (on-chain metric) |
| **Smart Money** | Wallets with historically successful trading records |
| **TVL** | Total Value Locked (in DeFi protocols) |

---

## Appendix B: Reference Documents

- [Comprehensive_Data_INDEX.md](./Comprehensive_Data_INDEX.md)
- [Comprehensive_Data_EXECUTIVE_SUMMARY.md](./Comprehensive_Data_EXECUTIVE_SUMMARY.md)
- [Comprehensive_Data_QUICKSTART.md](./Comprehensive_Data_QUICKSTART.md)
- [Comprehensive_Data_ARCHITECTURE.md](./Comprehensive_Data_ARCHITECTURE.md)
- [Comprehensive_Data_IMPLEMENTATION_PLAN.md](./Comprehensive_Data_IMPLEMENTATION_PLAN.md)

---

**Document Status**: Complete  
**Last Updated**: 2025-11-16  
**Version**: 1.0
