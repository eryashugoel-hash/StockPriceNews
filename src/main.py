"""
Entry-point for the Stock & Commodity News Intelligence Agent.

Run with::

    python -m src.main
"""

from __future__ import annotations

import logging
import sys
import time
import ssl

import certifi
import os
os.environ['SSL_CERT_FILE'] = certifi.where()
ssl._create_default_https_context = ssl._create_unverified_context

from src.analyzer.gemini_analyzer import GeminiAnalyzer
from src.collectors.base_collector import NewsItem
from src.collectors.financial_rss import FinancialRSSCollector
from src.collectors.google_news import GoogleNewsCollector
from src.collectors.reddit_collector import RedditCollector
from src.collectors.twitter_collector import TwitterCollector
from src.site_generator.generator import SiteGenerator
from src.utils.helpers import format_ist_datetime, get_ist_now, setup_logging

logger = logging.getLogger(__name__)


def _run_pipeline() -> None:
    """Execute the full collect → analyse → generate pipeline."""

    start = time.monotonic()
    now = get_ist_now()
    logger.info("=" * 70)
    logger.info(
        "Pipeline started at %s",
        format_ist_datetime(now),
    )
    logger.info("=" * 70)

    # ------------------------------------------------------------------
    # 1. Collect
    # ------------------------------------------------------------------
    collectors = [
        GoogleNewsCollector(),
        FinancialRSSCollector(),
        TwitterCollector(),
        RedditCollector(),
    ]

    all_news: list[NewsItem] = []
    all_tweets: list[NewsItem] = []

    for collector in collectors:
        try:
            items = collector.collect()
            if collector.name == "Twitter":
                all_tweets.extend(items)
            else:
                all_news.extend(items)
            logger.info(
                "✓ %s collected %d items", collector.name, len(items)
            )
        except Exception:
            logger.exception(
                "✗ %s collector failed — continuing with remaining collectors",
                collector.name,
            )

    logger.info("-" * 70)
    logger.info(
        "Collection complete: %d news items, %d tweets",
        len(all_news),
        len(all_tweets),
    )
    logger.info("-" * 70)

    # ------------------------------------------------------------------
    # 2. Analyse
    # ------------------------------------------------------------------
    try:
        analyzer = GeminiAnalyzer()
        insights_data = analyzer.analyze(all_news, all_tweets)
    except EnvironmentError as exc:
        logger.error("Analyzer init failed: %s", exc)
        logger.error(
            "Set the GEMINI_API_KEY environment variable and re-run."
        )
        sys.exit(1)
    except Exception:
        logger.exception("Analysis failed — aborting pipeline")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Generate site data
    # ------------------------------------------------------------------
    try:
        generator = SiteGenerator()
        generator.generate(insights_data)
    except Exception:
        logger.exception("Site generation failed")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    elapsed = time.monotonic() - start
    logger.info("=" * 70)
    logger.info(
        "Pipeline finished in %.1f s  |  %d insights generated",
        elapsed,
        len(insights_data.get("insights", [])),
    )
    logger.info("=" * 70)


def main() -> None:
    """Top-level entry point with global exception guard."""
    setup_logging()
    try:
        _run_pipeline()
    except KeyboardInterrupt:
        logger.info("Interrupted by user — exiting")
        sys.exit(130)
    except Exception:
        logger.exception("Unhandled exception in pipeline")
        sys.exit(1)


if __name__ == "__main__":
    main()
