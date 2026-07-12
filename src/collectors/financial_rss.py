"""
Financial RSS feed collector.

Parses RSS feeds from MoneyControl, Economic Times, Reuters, LiveMint,
NDTV Profit, etc.  Tags articles by matching watchlist terms in the
title or summary so downstream analysis knows which assets are affected.
"""

from __future__ import annotations

import logging
import time
from calendar import timegm
from datetime import datetime, timezone
from typing import Any

import feedparser  # type: ignore[import-untyped]

from src.collectors.base_collector import BaseCollector, NewsItem
from src.config import (
    FINANCIAL_RSS_FEEDS,
    NEWS_LOOKBACK_HOURS,
    WATCHLIST_COMMODITIES,
    WATCHLIST_STOCKS,
)
from src.utils.helpers import deduplicate_by_title

logger = logging.getLogger(__name__)


class FinancialRSSCollector(BaseCollector):
    """Collect news from curated financial RSS feeds."""

    @property
    def name(self) -> str:
        return "FinancialRSS"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def collect(self) -> list[NewsItem]:
        all_items: list[NewsItem] = []
        logger.info(
            "[%s] Parsing %d financial feeds …",
            self.name,
            len(FINANCIAL_RSS_FEEDS),
        )

        for source_name, feed_url in FINANCIAL_RSS_FEEDS.items():
            try:
                items = self._parse_feed(source_name, feed_url)
                all_items.extend(items)
                logger.info(
                    "[%s] %s → %d items", self.name, source_name, len(items)
                )
            except Exception:
                logger.exception(
                    "[%s] Failed to parse feed %s (%s)",
                    self.name,
                    source_name,
                    feed_url,
                )
            # Small delay between feeds
            time.sleep(0.2)

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
    def _parse_feed(
        self, source_name: str, feed_url: str
    ) -> list[NewsItem]:
        feed: Any = feedparser.parse(feed_url)

        if feed.bozo and not feed.entries:
            logger.warning(
                "[%s] Bozo error for %s: %s",
                self.name,
                source_name,
                feed.bozo_exception,
            )
            return []

        cutoff = datetime.now(tz=timezone.utc).timestamp() - (
            NEWS_LOOKBACK_HOURS * 3600
        )

        items: list[NewsItem] = []
        for entry in feed.entries:
            # --- time filter ---
            published_ts = self._entry_timestamp(entry)
            if published_ts is not None and published_ts < cutoff:
                continue

            title: str = entry.get("title", "").strip()
            summary: str = entry.get("summary", "").strip()
            link: str = entry.get("link", "")
            pub_str: str = entry.get("published", "")

            if not title:
                continue

            tags = self._match_tags(title, summary)

            items.append(
                NewsItem(
                    title=title,
                    summary=summary,
                    source=source_name,
                    url=link,
                    timestamp=pub_str,
                    tags=tags,
                )
            )

        return items

    # ------------------------------------------------------------------
    # Tag matching
    # ------------------------------------------------------------------
    @staticmethod
    def _match_tags(title: str, summary: str) -> list[str]:
        """Return watchlist terms that appear in the title or summary."""
        combined = (title + " " + summary).lower()
        matched: list[str] = []
        for term in WATCHLIST_STOCKS + WATCHLIST_COMMODITIES:
            if term.lower() in combined:
                matched.append(term)
        return matched

    @staticmethod
    def _entry_timestamp(entry: Any) -> float | None:
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if parsed:
            try:
                return float(timegm(parsed))
            except (TypeError, ValueError, OverflowError):
                pass
        return None
