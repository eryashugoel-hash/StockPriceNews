"""
Twitter / X collector via public Nitter RSS proxies.

For every account in ``TWITTER_ACCOUNTS``, tries each Nitter instance in
``NITTER_INSTANCES`` until one succeeds.  Tweets are filtered to the
lookback window and to financial keywords.

If *all* Nitter instances are unreachable the collector logs a warning
and returns an empty list — it never crashes the pipeline.
"""

from __future__ import annotations

import logging
import re
import time
from calendar import timegm
from datetime import datetime, timezone
from typing import Any

import feedparser  # type: ignore[import-untyped]

from src.collectors.base_collector import BaseCollector, NewsItem
from src.config import (
    NEWS_LOOKBACK_HOURS,
    NITTER_INSTANCES,
    TWITTER_ACCOUNTS,
)
from src.utils.helpers import deduplicate_by_title

logger = logging.getLogger(__name__)

# Keywords used to decide whether a tweet is "financial enough" to keep
_FINANCIAL_KEYWORDS: re.Pattern[str] = re.compile(
    r"\b("
    r"stock|market|trade|tariff|rate|gold|oil|economy|inflation|"
    r"gdp|fed|rbi|nifty|sensex|earnings|revenue|profit|loss|"
    r"bull|bear|crash|rally|commodity|silver|crude|natural gas|"
    r"interest rate|fiscal|monetary|rupee|dollar|forex|ipo|"
    r"dividend|buyback|merger|acquisition|regulation"
    r")\b",
    re.IGNORECASE,
)


class TwitterCollector(BaseCollector):
    """Collect recent financial tweets via Nitter RSS."""

    @property
    def name(self) -> str:
        return "Twitter"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def collect(self) -> list[NewsItem]:
        all_items: list[NewsItem] = []
        logger.info(
            "[%s] Fetching tweets for %d accounts …",
            self.name,
            len(TWITTER_ACCOUNTS),
        )

        for account in TWITTER_ACCOUNTS:
            try:
                items = self._fetch_account(account)
                all_items.extend(items)
            except Exception:
                logger.exception(
                    "[%s] Unexpected error for @%s", self.name, account
                )

        deduped = deduplicate_by_title(all_items)
        logger.info(
            "[%s] Collected %d tweets (%d after dedup)",
            self.name,
            len(all_items),
            len(deduped),
        )
        return deduped

    # ------------------------------------------------------------------
    # Per-account fetch with Nitter fallback
    # ------------------------------------------------------------------
    def _fetch_account(self, username: str) -> list[NewsItem]:
        """Try each Nitter instance in order; return tweets from the first
        instance that responds successfully."""
        for instance in NITTER_INSTANCES:
            url = f"https://{instance}/{username}/rss"
            try:
                import socket
                old_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(5.0)
                try:
                    feed: Any = feedparser.parse(url)
                finally:
                    socket.setdefaulttimeout(old_timeout)
                    
                if feed.bozo and not feed.entries:
                    logger.debug(
                        "[%s] Instance %s bozo for @%s: %s",
                        self.name,
                        instance,
                        username,
                        feed.bozo_exception,
                    )
                    continue

                items = self._parse_entries(feed.entries, username)
                if items or feed.entries:
                    # Instance responded — even if no recent tweets
                    logger.debug(
                        "[%s] %s served @%s (%d items)",
                        self.name,
                        instance,
                        username,
                        len(items),
                    )
                    return items

            except Exception:
                logger.debug(
                    "[%s] Instance %s unreachable for @%s",
                    self.name,
                    instance,
                    username,
                    exc_info=True,
                )
            # Small delay before trying next instance
            time.sleep(0.3)

        logger.warning(
            "[%s] All Nitter instances failed for @%s — skipping",
            self.name,
            username,
        )
        return []

    # ------------------------------------------------------------------
    # Entry parsing & filtering
    # ------------------------------------------------------------------
    def _parse_entries(
        self, entries: list[Any], username: str
    ) -> list[NewsItem]:
        cutoff = datetime.now(tz=timezone.utc).timestamp() - (
            NEWS_LOOKBACK_HOURS * 3600
        )

        items: list[NewsItem] = []
        for entry in entries:
            pub_ts = self._entry_timestamp(entry)
            if pub_ts is not None and pub_ts < cutoff:
                continue

            title: str = entry.get("title", "").strip()
            summary: str = entry.get("summary", "").strip()
            text = title or summary

            if not text:
                continue

            # Keep only financially relevant tweets
            if not _FINANCIAL_KEYWORDS.search(text):
                continue

            items.append(
                NewsItem(
                    title=text[:280],
                    summary=summary[:500] if summary else text[:500],
                    source=f"Twitter (@{username})",
                    url=entry.get("link", ""),
                    timestamp=entry.get("published", ""),
                    tags=[f"@{username}"],
                )
            )

        return items

    @staticmethod
    def _entry_timestamp(entry: Any) -> float | None:
        parsed = entry.get("published_parsed")
        if parsed:
            try:
                return float(timegm(parsed))
            except (TypeError, ValueError, OverflowError):
                pass
        return None
