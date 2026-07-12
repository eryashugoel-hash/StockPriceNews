"""
Google News RSS collector.

Builds search queries from the configured watchlists and macro topics,
fetches Google News RSS for each, and returns deduplicated ``NewsItem`` list.
"""

from __future__ import annotations

import logging
import time
from calendar import timegm
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

import feedparser  # type: ignore[import-untyped]

from src.collectors.base_collector import BaseCollector, NewsItem
from src.config import (
    MACRO_TOPICS,
    NEWS_LOOKBACK_HOURS,
    WATCHLIST_COMMODITIES,
    WATCHLIST_STOCKS,
)
from src.utils.helpers import deduplicate_by_title

logger = logging.getLogger(__name__)

_GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
)


class GoogleNewsCollector(BaseCollector):
    """Collect financial news via Google News RSS search."""

    @property
    def name(self) -> str:
        return "GoogleNews"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def collect(self) -> list[NewsItem]:
        """Search Google News for every watchlist term and macro topic."""
        all_items: list[NewsItem] = []
        queries = self._build_queries()
        logger.info("[%s] Searching %d queries …", self.name, len(queries))

        for query, tag in queries:
            try:
                items = self._fetch_feed(query, tag)
                all_items.extend(items)
            except Exception:
                logger.exception(
                    "[%s] Failed to fetch query %r", self.name, query
                )

        deduped = deduplicate_by_title(all_items)
        logger.info(
            "[%s] Collected %d items (%d after dedup)",
            self.name,
            len(all_items),
            len(deduped),
        )
        return deduped

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _build_queries() -> list[tuple[str, str]]:
        """Return ``(search_query, tag)`` pairs."""
        queries: list[tuple[str, str]] = []
        for stock in WATCHLIST_STOCKS:
            queries.append((f"{stock} stock market news", stock))
        for commodity in WATCHLIST_COMMODITIES:
            queries.append((f"{commodity} price commodity news", commodity))
        for topic in MACRO_TOPICS:
            queries.append((topic, topic))
        return queries

    def _fetch_feed(self, query: str, tag: str) -> list[NewsItem]:
        """Fetch a single Google News RSS feed and parse entries."""
        url = _GOOGLE_NEWS_RSS.format(query=quote_plus(query))
        feed: Any = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            logger.warning(
                "[%s] Feed error for %r: %s", self.name, query, feed.bozo_exception
            )
            return []

        cutoff = datetime.now(tz=timezone.utc).timestamp() - (
            NEWS_LOOKBACK_HOURS * 3600
        )

        items: list[NewsItem] = []
        for entry in feed.entries:
            published_ts = self._entry_timestamp(entry)
            if published_ts is not None and published_ts < cutoff:
                continue  # older than lookback window

            title: str = entry.get("title", "").strip()
            summary: str = entry.get("summary", "").strip()
            link: str = entry.get("link", "")
            pub_str: str = entry.get("published", "")

            if not title:
                continue

            items.append(
                NewsItem(
                    title=title,
                    summary=summary,
                    source=f"GoogleNews ({tag})",
                    url=link,
                    timestamp=pub_str,
                    tags=[tag],
                )
            )

        # Small courtesy delay to avoid hammering Google
        time.sleep(0.3)
        return items

    @staticmethod
    def _entry_timestamp(entry: Any) -> float | None:
        """Extract a UNIX timestamp from a feed entry, or *None*."""
        parsed = entry.get("published_parsed")
        if parsed:
            try:
                return float(timegm(parsed))
            except (TypeError, ValueError, OverflowError):
                pass
        return None
