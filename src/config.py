"""
Configuration module for the Stock & Commodity News Intelligence Agent.

Centralizes all watchlists, feed URLs, API settings, and environment
variable loading so every other module imports from one place.
"""

import os
from typing import Final
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Watchlists
# ---------------------------------------------------------------------------
WATCHLIST_STOCKS: Final[list[str]] = [
    "TCS",
    "HDFC Bank",
    "Reliance",
    "Infosys",
    "TATA Motors",
]

WATCHLIST_COMMODITIES: Final[list[str]] = [
    "Gold",
    "Silver",
    "Crude Oil",
    "Natural Gas",
]

MACRO_TOPICS: Final[list[str]] = [
    "fed rate cut",
    "rbi policy",
    "tariff trade war",
    "inflation data",
    "gdp growth",
    "unemployment",
]

# ---------------------------------------------------------------------------
# Social-media accounts & subreddits
# ---------------------------------------------------------------------------
TWITTER_ACCOUNTS: Final[list[str]] = [
    "realDonaldTrump",
    "elonmusk",
    "RBI",
    "nsaborwal",
    "WarrenBuffett",
]

REDDIT_SUBREDDITS: Final[list[str]] = [
    "IndianStockMarket",
    "wallstreetbets",
    "stocks",
]

# ---------------------------------------------------------------------------
# Nitter instances (public, rotating fallbacks)
# ---------------------------------------------------------------------------
NITTER_INSTANCES: Final[list[str]] = [
    "nitter.poast.org",
    "nitter.privacydev.net",
    "nitter.woodland.cafe",
]

# ---------------------------------------------------------------------------
# Financial RSS feeds
# ---------------------------------------------------------------------------
FINANCIAL_RSS_FEEDS: Final[dict[str, str]] = {
    "MoneyControl": "https://www.moneycontrol.com/rss/marketreports.xml",
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Reuters": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
    "LiveMint": "https://www.livemint.com/rss/markets",
    "NDTV Profit": "https://feeds.feedburner.com/ndtvprofit-latest",
}

# ---------------------------------------------------------------------------
# Gemini AI settings
# ---------------------------------------------------------------------------
GEMINI_MODEL: Final[str] = "gemini-flash-latest"

# ---------------------------------------------------------------------------
# Pipeline tunables
# ---------------------------------------------------------------------------
NEWS_LOOKBACK_HOURS: Final[int] = 24
MAX_INSIGHTS: Final[int] = 5

# ---------------------------------------------------------------------------
# API keys (loaded from environment)
# ---------------------------------------------------------------------------
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
