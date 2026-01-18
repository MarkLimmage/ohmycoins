/**
 * Rate Limiting Load Test
 * 
 * Sprint 2.12 - Track B: Performance Testing
 * 
 * Tests rate limiting middleware under load:
 * - 60 req/min per-user limit
 * - 1000 req/hour per-user limit  
 * - Admin multiplier (5x)
 * - Redis performance under load
 * - 100 concurrent users
 * 
 * Requirements:
 * - k6 (https://k6.io/)
 * - Backend service running with rate limiting enabled
 * - Redis running
 * 
 * Usage:
 *   k6 run load_test_rate_limiting.js
 *   k6 run --vus 100 --duration 5m load_test_rate_limiting.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const rateLimitHits = new Counter('rate_limit_hits');
const rateLimitRemaining = new Trend('rate_limit_remaining');
const rateLimitReset = new Trend('rate_limit_reset_time');
const requestDuration = new Trend('request_duration');
const rateLimitViolations = new Rate('rate_limit_violations');

// Test configuration
export const options = {
    scenarios: {
        // Scenario 1: Test per-minute rate limit (60 req/min for normal users)
        per_minute_limit: {
            executor: 'constant-arrival-rate',
            duration: '2m',
            rate: 70, // Attempt 70 req/min to trigger rate limit
            timeUnit: '1m',
            preAllocatedVUs: 10,
            maxVUs: 20,
            exec: 'testPerMinuteLimit',
            tags: { scenario: 'per_minute_limit' },
        },
        
        // Scenario 2: Test per-hour rate limit (1000 req/hour for normal users)
        per_hour_limit: {
            executor: 'constant-arrival-rate',
            duration: '5m',
            rate: 250, // 1000/hour = ~250 per 5 min chunk, test slightly over
            timeUnit: '5m',
            preAllocatedVUs: 30,
            maxVUs: 50,
            exec: 'testPerHourLimit',
            tags: { scenario: 'per_hour_limit' },
            startTime: '2m', // Start after per_minute_limit completes
        },
        
        // Scenario 3: Test admin multiplier (300 req/min, 10000 req/hour)
        admin_multiplier: {
            executor: 'constant-arrival-rate',
            duration: '2m',
            rate: 350, // Attempt 350 req/min to test admin 5x multiplier
            timeUnit: '1m',
            preAllocatedVUs: 20,
            maxVUs: 40,
            exec: 'testAdminMultiplier',
            tags: { scenario: 'admin_multiplier' },
            startTime: '7m', // Start after previous scenarios
        },
        
        // Scenario 4: Test concurrent users (100 concurrent)
        concurrent_users: {
            executor: 'constant-vus',
            vus: 100,
            duration: '3m',
            exec: 'testConcurrentUsers',
            tags: { scenario: 'concurrent_users' },
            startTime: '9m', // Start after admin test
        },
        
        // Scenario 5: Redis performance under sustained load
        redis_performance: {
            executor: 'ramping-arrival-rate',
            startRate: 100,
            timeUnit: '1m',
            preAllocatedVUs: 50,
            maxVUs: 150,
            stages: [
                { duration: '2m', target: 500 },  // Ramp up to 500 req/min
                { duration: '3m', target: 1000 }, // Ramp to 1000 req/min
                { duration: '2m', target: 500 },  // Ramp down
                { duration: '1m', target: 100 },  // Back to baseline
            ],
            exec: 'testRedisPerformance',
            tags: { scenario: 'redis_performance' },
            startTime: '12m', // Start after concurrent test
        },
    },
    
    thresholds: {
        // Overall success rate should be high (allowing for expected 429s)
        'http_req_failed': ['rate<0.5'], // Less than 50% failures (429s are expected)
        
        // Response times
        'http_req_duration': ['p(95)<500', 'p(99)<1000'], // 95th percentile under 500ms
        
        // Rate limiting metrics
        'rate_limit_hits': ['count>0'], // Should hit rate limits
        'rate_limit_remaining': ['avg>=0'], // Should track remaining requests
        
        // Redis should handle load efficiently
        'request_duration{scenario:redis_performance}': ['p(95)<100'], // Redis ops under 100ms
    },
};

// Base URL - configure for your environment
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Test users (these should be pre-created in the test database)
const NORMAL_USER = {
    username: 'test@example.com',
    password: 'TestPassword123!',
    token: null,
};

const ADMIN_USER = {
    username: 'admin@example.com',
    password: 'AdminPassword123!',
    token: null,
    is_superuser: true,
};

/**
 * Setup: Authenticate users before tests
 */
export function setup() {
    // Login normal user
    const normalLogin = http.post(`${BASE_URL}/api/v1/login/access-token`, {
        username: NORMAL_USER.username,
        password: NORMAL_USER.password,
    });
    
    if (normalLogin.status === 200) {
        NORMAL_USER.token = normalLogin.json('access_token');
    }
    
    // Login admin user
    const adminLogin = http.post(`${BASE_URL}/api/v1/login/access-token`, {
        username: ADMIN_USER.username,
        password: ADMIN_USER.password,
    });
    
    if (adminLogin.status === 200) {
        ADMIN_USER.token = adminLogin.json('access_token');
    }
    
    return { normalToken: NORMAL_USER.token, adminToken: ADMIN_USER.token };
}

/**
 * Test per-minute rate limit (60 req/min for normal users)
 */
export function testPerMinuteLimit(data) {
    const headers = {
        'Authorization': `Bearer ${data.normalToken}`,
        'Content-Type': 'application/json',
    };
    
    const startTime = Date.now();
    const response = http.get(`${BASE_URL}/api/v1/users/me`, { headers });
    const duration = Date.now() - startTime;
    
    requestDuration.add(duration);
    
    // Check rate limit headers
    const rateLimitLimit = response.headers['X-Ratelimit-Limit'];
    const remaining = response.headers['X-Ratelimit-Remaining'];
    const reset = response.headers['X-Ratelimit-Reset'];
    
    if (remaining) {
        rateLimitRemaining.add(parseInt(remaining));
    }
    
    const checks = check(response, {
        'status is 200 or 429': (r) => r.status === 200 || r.status === 429,
        'has rate limit headers': (r) => 
            r.headers['X-Ratelimit-Limit'] !== undefined,
    });
    
    // Track rate limit hits
    if (response.status === 429) {
        rateLimitHits.add(1);
        rateLimitViolations.add(1);
        
        // Check for Retry-After header
        check(response, {
            'has Retry-After header on 429': (r) =>
                r.headers['Retry-After'] !== undefined,
        });
        
        // Respect Retry-After header
        const retryAfter = parseInt(response.headers['Retry-After'] || '1');
        sleep(retryAfter);
    } else {
        rateLimitViolations.add(0);
    }
}

/**
 * Test per-hour rate limit (1000 req/hour for normal users)
 */
export function testPerHourLimit(data) {
    const headers = {
        'Authorization': `Bearer ${data.normalToken}`,
        'Content-Type': 'application/json',
    };
    
    const response = http.get(`${BASE_URL}/api/v1/users/me/llm-credentials`, { headers });
    
    check(response, {
        'status is 200 or 429': (r) => r.status === 200 || r.status === 429,
        'rate limit headers present': (r) =>
            r.headers['X-Ratelimit-Limit'] && r.headers['X-Ratelimit-Remaining'],
    });
    
    if (response.status === 429) {
        rateLimitHits.add(1);
        
        // Verify hour-based limit is enforced
        const remaining = parseInt(response.headers['X-Ratelimit-Remaining'] || '0');
        check(response, {
            'hour limit enforced': () => remaining === 0,
        });
    }
    
    sleep(0.1); // Small delay between requests
}

/**
 * Test admin multiplier (5x limits: 300 req/min, 10000 req/hour)
 */
export function testAdminMultiplier(data) {
    const headers = {
        'Authorization': `Bearer ${data.adminToken}`,
        'Content-Type': 'application/json',
    };
    
    const response = http.get(`${BASE_URL}/api/v1/users/me`, { headers });
    
    check(response, {
        'admin request successful': (r) => r.status === 200 || r.status === 429,
        'has rate limit headers': (r) => r.headers['X-Ratelimit-Limit'] !== undefined,
    });
    
    // Admin should have higher limits (5x multiplier)
    const limit = parseInt(response.headers['X-Ratelimit-Limit'] || '0');
    
    if (limit > 0) {
        check(response, {
            'admin has 5x multiplier (300/min)': () => limit === 300 || limit === 10000,
        });
    }
    
    if (response.status === 429) {
        rateLimitHits.add(1);
    }
}

/**
 * Test concurrent users (100 concurrent)
 */
export function testConcurrentUsers(data) {
    const headers = {
        'Authorization': `Bearer ${data.normalToken}`,
        'Content-Type': 'application/json',
    };
    
    // Simulate realistic user behavior with multiple endpoints
    const endpoints = [
        '/api/v1/users/me',
        '/api/v1/users/me/llm-credentials',
    ];
    
    const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
    const response = http.get(`${BASE_URL}${endpoint}`, { headers });
    
    check(response, {
        'concurrent request handled': (r) => r.status === 200 || r.status === 429,
        'response time acceptable': (r) => r.timings.duration < 1000,
    });
    
    if (response.status === 429) {
        rateLimitHits.add(1);
        sleep(2); // Back off when rate limited
    } else {
        sleep(Math.random() * 0.5); // Random delay 0-500ms
    }
}

/**
 * Test Redis performance under sustained load
 */
export function testRedisPerformance(data) {
    const headers = {
        'Authorization': `Bearer ${data.normalToken}`,
        'Content-Type': 'application/json',
    };
    
    const startTime = Date.now();
    const response = http.get(`${BASE_URL}/api/v1/users/me`, { headers });
    const duration = Date.now() - startTime;
    
    requestDuration.add(duration);
    
    // Redis operations should be fast (<10ms target)
    check(response, {
        'Redis latency <100ms': () => duration < 100,
        'Redis latency <50ms': () => duration < 50,
        'Redis latency <10ms': () => duration < 10,
    });
    
    if (response.status === 429) {
        rateLimitHits.add(1);
        sleep(1);
    }
}

/**
 * Teardown: Summary report
 */
export function teardown(data) {
    console.log('\n=== Rate Limiting Load Test Summary ===');
    console.log(`Normal user token: ${data.normalToken ? 'OK' : 'FAILED'}`);
    console.log(`Admin user token: ${data.adminToken ? 'OK' : 'FAILED'}`);
    console.log('==========================================\n');
}

/**
 * Default test function (if running without scenarios)
 */
export default function (data) {
    testPerMinuteLimit(data);
}
