# mypy: ignore-errors
"""
Rate Limiting Middleware

Sprint 2.11 - Track B: Rate Limiting Implementation

Provides user-based rate limiting with Redis backend:
- Per-user rate limits (60 req/min for normal users, 300 req/min for admins)
- Rate limit headers in responses (X-RateLimit-*)
- 429 Too Many Requests responses with Retry-After header
- Bypass prevention (rate limits by user_id, not IP or token)

Security Features:
- OWASP A04:2021 – Insecure Design (abuse prevention)
- OWASP A05:2021 – Security Misconfiguration (proper rate limiting)
"""

import time
from collections.abc import Callable

import jwt
import redis
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis for tracking.

    Implements per-user rate limits with different windows:
    - Per-minute limits: 60 requests for normal users, 300 for admins
    - Per-hour limits: 1000 requests for normal users, 10000 for admins

    Rate limits are tied to user_id (not IP or token) to prevent bypass.
    """

    def __init__(self, app, redis_url: str = None):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)

        # Rate limit configuration from settings
        self.normal_user_limits = {
            "minute": settings.RATE_LIMIT_PER_MINUTE,
            "hour": settings.RATE_LIMIT_PER_HOUR,
        }
        self.admin_multiplier = settings.RATE_LIMIT_ADMIN_MULTIPLIER

    def get_user_id_from_token(self, request: Request) -> tuple[str | None, bool]:
        """
        Extract user_id and is_superuser from JWT token.

        Returns:
            (user_id, is_superuser) tuple, or (None, False) if no valid token
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None, False

        token = auth_header.replace("Bearer ", "")
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            user_id = payload.get("sub")
            is_superuser = payload.get("is_superuser", False)
            return user_id, is_superuser
        except (jwt.DecodeError, jwt.ExpiredSignatureError, KeyError):
            return None, False

    def get_rate_limits(self, is_superuser: bool) -> dict:
        """Get rate limits based on user role."""
        if is_superuser:
            return {
                "minute": self.normal_user_limits["minute"] * self.admin_multiplier,
                "hour": self.normal_user_limits["hour"] * self.admin_multiplier,
            }
        return self.normal_user_limits

    def check_rate_limit(
        self,
        user_id: str,
        window: str,
        limit: int
    ) -> tuple[bool, int, int]:
        """
        Check if user is within rate limit for given window.

        Args:
            user_id: User identifier
            window: Time window ("minute" or "hour")
            limit: Maximum requests allowed in window

        Returns:
            (allowed, remaining, reset_time) tuple
            - allowed: True if request is allowed
            - remaining: Requests remaining in window
            - reset_time: Unix timestamp when limit resets
        """
        current_time = int(time.time())

        # Calculate window parameters
        if window == "minute":
            window_size = 60
            window_start = current_time - (current_time % 60)
        elif window == "hour":
            window_size = 3600
            window_start = current_time - (current_time % 3600)
        else:
            raise ValueError(f"Invalid window: {window}")

        reset_time = window_start + window_size
        key = f"rate_limit:{user_id}:{window}:{window_start}"

        # Increment counter atomically
        try:
            count = self.redis_client.incr(key)

            # Set expiration on first request of window
            if count == 1:
                self.redis_client.expire(key, window_size)

            # Check if limit exceeded
            allowed = count <= limit
            remaining = max(0, limit - count)

            return allowed, remaining, reset_time

        except redis.RedisError:
            # If Redis fails, allow request but don't enforce limits
            # Log error in production
            return True, limit, reset_time

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""

        # Skip rate limiting for health check and docs endpoints
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Get user from token
        user_id, is_superuser = self.get_user_id_from_token(request)

        # Skip rate limiting for unauthenticated requests (handled by auth)
        if not user_id:
            return await call_next(request)

        # Get rate limits for user role
        limits = self.get_rate_limits(is_superuser)

        # Check both minute and hour limits
        minute_allowed, minute_remaining, minute_reset = self.check_rate_limit(
            user_id, "minute", limits["minute"]
        )
        hour_allowed, hour_remaining, hour_reset = self.check_rate_limit(
            user_id, "hour", limits["hour"]
        )

        # Use the most restrictive limit
        if not minute_allowed:
            # Rate limit exceeded for minute window
            retry_after = minute_reset - int(time.time())
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={
                    "X-RateLimit-Limit": str(limits["minute"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(minute_reset),
                    "Retry-After": str(retry_after),
                }
            )

        if not hour_allowed:
            # Rate limit exceeded for hour window
            retry_after = hour_reset - int(time.time())
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={
                    "X-RateLimit-Limit": str(limits["hour"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(hour_reset),
                    "Retry-After": str(retry_after),
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limits["minute"])
        response.headers["X-RateLimit-Remaining"] = str(minute_remaining)
        response.headers["X-RateLimit-Reset"] = str(minute_reset)

        return response
