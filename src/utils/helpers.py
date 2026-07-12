"""
Shared helper utilities — logging setup, retry logic, time handling,
and lightweight deduplication.
"""

from __future__ import annotations

import functools
import logging
import time
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Any, Callable, TypeVar

# IST offset (UTC+05:30) — avoids a pytz / zoneinfo dependency
IST = timezone(timedelta(hours=5, minutes=30))

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def setup_logging(level: int = logging.INFO) -> None:
    """Configure structured logging with ISO-8601 timestamps."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)-28s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    # Quieten noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("feedparser").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Retry decorator
# ---------------------------------------------------------------------------
def retry_with_backoff(
    func: Callable[..., T] | None = None,
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> Callable[..., T]:
    """Decorator that retries *func* with exponential back-off.

    Can be used with or without arguments::

        @retry_with_backoff
        def my_func(): ...

        @retry_with_backoff(max_retries=5, base_delay=2.0)
        def my_func(): ...
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            logger = logging.getLogger(fn.__module__)
            last_exc: Exception | None = None
            for attempt in range(1, max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        delay = base_delay * (2 ** (attempt - 1))
                        logger.warning(
                            "%s attempt %d/%d failed (%s). Retrying in %.1fs …",
                            fn.__name__,
                            attempt,
                            max_retries,
                            exc,
                            delay,
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            fn.__name__,
                            max_retries,
                            exc,
                        )
            raise last_exc  # type: ignore[misc]

        return wrapper

    # Allow bare `@retry_with_backoff` (no parentheses)
    if func is not None:
        return decorator(func)
    return decorator  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Time utilities
# ---------------------------------------------------------------------------
def get_ist_now() -> datetime:
    """Return the current datetime in IST."""
    return datetime.now(tz=IST)


def format_ist_datetime(dt: datetime) -> str:
    """Format a datetime as an ISO-8601 string in IST."""
    return dt.astimezone(IST).strftime("%Y-%m-%dT%H:%M:%S+05:30")


def is_within_lookback(
    timestamp_str: str,
    hours: int = 24,
    *,
    formats: tuple[str, ...] | None = None,
) -> bool:
    """Return *True* if *timestamp_str* falls within the last *hours*.

    Tries several common date formats; returns *False* on parse failure
    so the caller can decide whether to keep the item.
    """
    if formats is None:
        formats = (
            "%a, %d %b %Y %H:%M:%S %z",   # RFC-2822  (RSS default)
            "%a, %d %b %Y %H:%M:%S %Z",   # with tz name
            "%Y-%m-%dT%H:%M:%S%z",         # ISO-8601
            "%Y-%m-%dT%H:%M:%S.%f%z",      # ISO-8601 with microseconds
            "%Y-%m-%d %H:%M:%S",            # naive (assumed UTC)
        )
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours)

    for fmt in formats:
        try:
            parsed = datetime.strptime(timestamp_str.strip(), fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed >= cutoff
        except ValueError:
            continue

    # If none of the formats matched, log a debug message and return False
    logging.getLogger(__name__).debug(
        "Could not parse timestamp: %r", timestamp_str
    )
    return False


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------
def deduplicate_by_title(
    items: list[Any],
    threshold: float = 0.7,
) -> list[Any]:
    """Remove near-duplicate items based on ``title`` similarity.

    Each item must have a ``.title`` attribute (e.g. a ``NewsItem``).
    Uses ``SequenceMatcher`` for a quick ratio comparison.
    """
    if not items:
        return []

    unique: list[Any] = [items[0]]
    for candidate in items[1:]:
        is_dup = False
        for existing in unique:
            ratio = SequenceMatcher(
                None,
                candidate.title.lower(),
                existing.title.lower(),
            ).quick_ratio()
            if ratio >= threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(candidate)
    return unique
