"""
Reddit API collector plugin for community sentiment (Human Ledger).

This collector fetches cryptocurrency discussions from Reddit, including
post bodies and top comments, to provide rich conversation data for
downstream sentiment enrichment.

Supports OAuth2 app-only auth for higher rate limits, with graceful
fallback to public API.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.core.config import HTTP_USER_AGENT, settings
from app.models import SocialSentiment

logger = logging.getLogger(__name__)


class HumanReddit(ICollector):
    """Collector for cryptocurrency discussions from Reddit with deep comment fetching."""

    MONITORED_SUBREDDITS = [
        "CryptoCurrency",
        "Bitcoin",
        "ethereum",
        "CryptoMarkets",
        "altcoin",
    ]

    # OAuth token cache
    _oauth_token: str | None = None
    _oauth_token_expires: float = 0.0

    @property
    def name(self) -> str:
        return "human_reddit"

    @property
    def description(self) -> str:
        return "Reddit crypto community sentiment from r/CryptoCurrency and related subreddits"

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subreddits": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Subreddits to monitor",
                    "default": self.MONITORED_SUBREDDITS,
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of posts to fetch per subreddit",
                    "default": 25,
                },
            },
            "required": [],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        if "subreddits" in config:
            if not isinstance(config["subreddits"], list):
                logger.error("Invalid config: 'subreddits' must be a list")
                return False
        if "limit" in config:
            try:
                int(config["limit"])
            except (ValueError, TypeError):
                logger.error("Invalid config: 'limit' must be an integer")
                return False
        return True

    def _has_oauth_credentials(self) -> bool:
        return bool(settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET)

    async def _get_oauth_token(self, session: aiohttp.ClientSession) -> str | None:
        """Fetch or return cached Reddit OAuth2 app-only token."""
        if self._oauth_token and time.monotonic() < self._oauth_token_expires:
            return self._oauth_token

        if not self._has_oauth_credentials():
            return None

        try:
            auth = aiohttp.BasicAuth(
                settings.REDDIT_CLIENT_ID,  # type: ignore[arg-type]
                settings.REDDIT_CLIENT_SECRET or "",
            )
            data = {"grant_type": "client_credentials"}
            headers = {"User-Agent": HTTP_USER_AGENT}
            async with session.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"Reddit OAuth token request failed: {resp.status}")
                    return None
                body = await resp.json()
                token = body.get("access_token")
                expires_in = body.get("expires_in", 3600)
                if token:
                    self._oauth_token = token
                    # Cache with 5-min safety margin
                    self._oauth_token_expires = time.monotonic() + expires_in - 300
                    logger.info("Reddit OAuth token acquired")
                    return token
                return None
        except Exception as e:
            logger.warning(f"Reddit OAuth token fetch failed: {e}")
            return None

    async def _rate_limited_sleep(
        self, resp: aiohttp.ClientResponse | None, use_oauth: bool
    ) -> None:
        """Sleep for rate-limit-appropriate duration, respecting Retry-After."""
        if resp is not None and resp.status == 429:
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = min(float(retry_after), 30.0)
                    logger.warning(f"Rate limited, waiting {wait}s (Retry-After)")
                    await asyncio.sleep(wait)
                    return
                except ValueError:
                    pass
        delay = 1.0 if use_oauth else 2.0
        await asyncio.sleep(delay)

    async def test_connection(self, config: dict[str, Any]) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": HTTP_USER_AGENT}
                async with session.get(
                    "https://www.reddit.com/r/CryptoCurrency/hot.json",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to test Reddit connection: {e}")
            return False

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        """Collect hot posts with bodies and top comments from monitored subreddits."""
        subreddits = config.get("subreddits", self.MONITORED_SUBREDDITS)
        limit = config.get("limit", 25)

        logger.info(f"Collecting posts from {len(subreddits)} subreddits")

        all_posts: list[SocialSentiment] = []
        seen_urls: set[str] = set()

        async with aiohttp.ClientSession() as session:
            oauth_token = await self._get_oauth_token(session)
            use_oauth = oauth_token is not None

            if use_oauth:
                base_url = "https://oauth.reddit.com"
                headers = {
                    "User-Agent": HTTP_USER_AGENT,
                    "Authorization": f"Bearer {oauth_token}",
                }
                logger.info("Using Reddit OAuth API (1 req/sec)")
            else:
                base_url = "https://www.reddit.com"
                headers = {"User-Agent": HTTP_USER_AGENT}
                logger.info("Using Reddit public API (2s delay)")

            for subreddit in subreddits:
                try:
                    await self._rate_limited_sleep(None, use_oauth)

                    url = f"{base_url}/r/{subreddit}/hot.json"
                    params: dict[str, int] = {"limit": limit, "raw_json": 1}

                    async with session.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        if resp.status == 429:
                            await self._rate_limited_sleep(resp, use_oauth)
                            continue
                        if resp.status != 200:
                            logger.warning(
                                f"Failed to fetch r/{subreddit}: status {resp.status}"
                            )
                            continue
                        data = await resp.json()

                    if not data or "data" not in data or "children" not in data["data"]:
                        logger.warning(f"No data returned for r/{subreddit}")
                        continue

                    posts = data["data"]["children"]
                    logger.info(f"Fetched {len(posts)} posts from r/{subreddit}")

                    for post in posts:
                        try:
                            post_data = post.get("data", {})
                            title = post_data.get("title", "")
                            created_utc = post_data.get("created_utc")

                            # Intra-run dedup by permalink
                            permalink = post_data.get("permalink", "")
                            if not permalink:
                                continue
                            post_url = f"https://reddit.com{permalink}"
                            if post_url in seen_urls:
                                continue
                            seen_urls.add(post_url)

                            # Parse publication timestamp
                            published_at = None
                            if created_utc:
                                try:
                                    published_at = datetime.fromtimestamp(
                                        created_utc, tz=timezone.utc
                                    )
                                except Exception:
                                    pass

                            # Extract post body and comment count
                            body = post_data.get("selftext") or None
                            num_comments = post_data.get("num_comments", 0)

                            # Fetch top comments for posts that have them
                            top_comments = None
                            if num_comments and num_comments > 0:
                                top_comments = await self._fetch_top_comments(
                                    session,
                                    base_url,
                                    headers,
                                    permalink,
                                    use_oauth,
                                )

                            data_point = SocialSentiment(
                                platform="reddit",
                                content=title,
                                author=post_data.get("author"),
                                score=post_data.get("score"),
                                sentiment=None,
                                currencies=None,
                                posted_at=published_at,
                                collected_at=datetime.now(timezone.utc),
                                body=body,
                                comment_count=num_comments,
                                top_comments=top_comments,
                            )

                            all_posts.append(data_point)

                        except Exception as e:
                            logger.debug(f"Failed to parse Reddit post: {e}")
                            continue

                except Exception as e:
                    logger.error(f"Failed to collect posts from r/{subreddit}: {e}")
                    continue

        logger.info(f"Collected {len(all_posts)} posts total")
        return all_posts

    async def _fetch_top_comments(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        headers: dict[str, str],
        permalink: str,
        use_oauth: bool,
    ) -> list[dict[str, Any]] | None:
        """Fetch top 10 comments by score for a post."""
        try:
            await self._rate_limited_sleep(None, use_oauth)

            url = f"{base_url}{permalink}.json"
            params = {"limit": 10, "sort": "best", "raw_json": 1}

            async with session.get(
                url,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 429:
                    await self._rate_limited_sleep(resp, use_oauth)
                    return None
                if resp.status != 200:
                    logger.debug(
                        f"Failed to fetch comments for {permalink}: {resp.status}"
                    )
                    return None
                data = await resp.json()

            # Reddit returns [post_listing, comments_listing]
            if not isinstance(data, list) or len(data) < 2:
                return None

            comments_listing = data[1]
            if (
                not comments_listing
                or "data" not in comments_listing
                or "children" not in comments_listing["data"]
            ):
                return None

            comments = []
            for child in comments_listing["data"]["children"]:
                if child.get("kind") != "t1":
                    continue
                c_data = child.get("data", {})
                comment_text = c_data.get("body", "")
                if not comment_text:
                    continue
                comments.append(
                    {
                        "text": comment_text,
                        "score": c_data.get("score", 0),
                        "author": c_data.get("author", "[deleted]"),
                    }
                )

            # Sort by score descending and take top 10
            comments.sort(key=lambda c: c["score"], reverse=True)
            return comments[:10] if comments else None

        except Exception as e:
            logger.debug(f"Failed to fetch comments for {permalink}: {e}")
            return None


CollectorRegistry.register(HumanReddit)
