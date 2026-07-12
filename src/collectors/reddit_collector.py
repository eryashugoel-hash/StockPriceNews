"""
Reddit collector — hot posts from financial subreddits.

Uses Reddit's public RSS endpoint (no API key required).  A custom
``User-Agent`` header is set to reduce 429 throttling.
"""

from __future__ import annotations

import logging
import time
from calendar import timegm
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, urlopen

import feedparser  # type: ignore[import-untyped]

from src.collectors.base_collector import BaseCollector, NewsItem
from src.config import NEWS_LOOKBACK_HOURS, REDDIT_SUBREDDITS
from src.utils.helpers import deduplicate_by_title

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "StockPriceNewsBot/1.0 "
    "(compatible; financial-news-aggregator; +https://github.com/example)"
)


class RedditCollector(BaseCollector):
    """Collect hot posts from configured subreddits via RSS."""

    @property
    def name(self) -> str:
        return "Reddit"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def collect(self) -> list[NewsItem]:
        all_items: list[NewsItem] = []
        logger.info(
            "[%s] Fetching from %d subreddits …",
            self.name,
            len(REDDIT_SUBREDDITS),
        )

        for subreddit in REDDIT_SUBREDDITS:
            try:
                items = self._fetch_subreddit(subreddit)
                all_items.extend(items)
                logger.info(
                    "[%s] r/%s → %d items", self.name, subreddit, len(items)
                )
            except Exception:
                logger.exception(
                    "[%s] Failed to fetch r/%s", self.name, subreddit
                )
            time.sleep(0.5)  # polite delay

        deduped = deduplicate_by_title(all_items)
        logger.info(
            "[%s] Total %d items (%d after dedup)",
            self.name,
            len(all_items),
            len(deduped),
        )
        return deduped

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _fetch_subreddit(self, subreddit: str) -> list[NewsItem]:
        url = f"https://www.reddit.com/r/{subreddit}/hot/.rss"
        xml_bytes = self._http_get(url)
        feed: Any = feedparser.parse(xml_bytes)

        if feed.bozo and not feed.entries:
            logger.warning(
                "[%s] Feed error for r/%s: %s",
                self.name,
                subreddit,
                feed.bozo_exception,
            )
            return []

        cutoff = datetime.now(tz=timezone.utc).timestamp() - (
            NEWS_LOOKBACK_HOURS * 3600
        )

        items: list[NewsItem] = []
        for entry in feed.entries:
            pub_ts = self._entry_timestamp(entry)
            if pub_ts is not None and pub_ts < cutoff:
                continue

            title: str = entry.get("title", "").strip()
            # Reddit RSS stores HTML content in content[0].value
            summary: str = ""
            content_list = entry.get("content")
            if content_list and isinstance(content_list, list):
                summary = content_list[0].get("value", "")[:500]
            if not summary:
                summary = entry.get("summary", "")[:500]

            link: str = entry.get("link", "")
            pub_str: str = entry.get("published", entry.get("updated", ""))

            if not title:
                continue

            items.append(
                NewsItem(
                    title=title,
                    summary=summary,
                    source=f"Reddit (r/{subreddit})",
                    url=link,
                    timestamp=pub_str,
                    tags=[f"r/{subreddit}"],
                )
            )

        return items

    # ------------------------------------------------------------------
    # HTTP helper (custom User-Agent)
    # ------------------------------------------------------------------
    @staticmethod
    def _http_get(url: str, timeout: int = 15) -> bytes:
        """Fetch *url* with a custom User-Agent to avoid 429s."""
        req = Request(url, headers={"User-Agent": _USER_AGENT})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read()  # type: ignore[no-any-return]

    @staticmethod
    def _entry_timestamp(entry: Any) -> float | None:
        for key in ("published_parsed", "updated_parsed"):
            parsed = entry.get(key)
            if parsed:
                try:
                    return float(timegm(parsed))
                except (TypeError, ValueError, OverflowError):
                    pass
        return None
