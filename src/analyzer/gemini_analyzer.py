"""
Gemini-powered market intelligence analyzer.

Single-call approach: send all collected news + tweets to Gemini and ask it
to pick the top N most market-moving items, returning a structured insight
for each (sentiment, confidence, affected assets, reasoning).

Resilience:
  * Retries transient errors (429 / 500 / 503 / 504, timeouts, bad JSON)
    with exponential back-off.
  * Falls back through ``GEMINI_FALLBACK_MODELS`` if the primary model is
    overloaded.

The output conforms to the JSON schema consumed by the frontend.
"""

from __future__ import annotations

import json
import logging
import textwrap
import time
from typing import Any

import httpx
from google import genai  # type: ignore[import-untyped]
from google.genai import errors as genai_errors  # type: ignore[import-untyped]
from google.genai import types  # type: ignore[import-untyped]

from src import config
from src.collectors.base_collector import NewsItem
from src.config import GEMINI_API_KEY, GEMINI_MODEL, MAX_INSIGHTS
from src.utils.helpers import format_ist_datetime, get_ist_now

logger = logging.getLogger(__name__)

# Optional fallback models (define GEMINI_FALLBACK_MODELS in config.py)
_FALLBACK_MODELS: list[str] = list(getattr(config, "GEMINI_FALLBACK_MODELS", []))

# Retry tunables
_ATTEMPTS_PER_MODEL = 3
_BASE_DELAY_SECONDS = 5.0
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_REQUEST_TIMEOUT_MS = 90_000

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = textwrap.dedent("""\
    You are a **Senior Financial Analyst** specializing in NEWS-DRIVEN
    market intelligence for Indian stocks, global commodities, and
    macroeconomic events.

    Your role:
    • Assess how each news item is likely to affect stock or commodity prices.
    • Consider second-order effects (e.g., a US tariff on IT services →
      TCS / Infosys bearish; RBI rate cut → banking stocks bullish).
    • Rate your **confidence** (0.0-1.0) based on source reliability,
      directness of impact, and historical precedent.
    • Classify sentiment as exactly one of: bullish, bearish, neutral.
    • Suggest an action: watch, buy_opportunity, or risk_alert.
    • Assign a category: stock_specific, commodity, macro, policy, geopolitical.

    You must NOT provide technical analysis (charts, RSI, MACD, etc.).
    Focus exclusively on how the *news* changes the fundamental outlook.

    Always include the following disclaimer in your output:
    "This is AI-generated analysis for informational purposes only.
     Not financial advice. Do your own research before investing."
""")

_TRIAGE_USER_PROMPT = textwrap.dedent("""\
    Below are all the news items and tweets collected in the last 24 hours.
    Identify the **top {max_insights}** most market-moving items.

    For each selected item return:
    - headline (original title)
    - source
    - url
    - affected_assets (list of stock / commodity names)
    - asset_type (stock | commodity | macro)
    - sentiment (bullish | bearish | neutral)
    - confidence (0.0 - 1.0)
    - reasoning (2-3 sentences)
    - action (watch | buy_opportunity | risk_alert)
    - category (stock_specific | commodity | macro | policy | geopolitical)

    Also extract up to 5 relevant tweets with:
    - author, text, relevance (one-line note on why it matters)

    ---
    NEWS ITEMS:
    {news_block}

    ---
    TWEETS:
    {tweet_block}
""")

# The JSON schema we ask Gemini to conform to
_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "date": {"type": "string"},
        "generated_at": {"type": "string"},
        "market_pulse": {
            "type": "object",
            "properties": {
                "bullish": {"type": "integer"},
                "bearish": {"type": "integer"},
                "neutral": {"type": "integer"},
            },
            "required": ["bullish", "bearish", "neutral"],
        },
        "insights": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "headline": {"type": "string"},
                    "source": {"type": "string"},
                    "url": {"type": "string"},
                    "affected_assets": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "asset_type": {"type": "string"},
                    "sentiment": {"type": "string"},
                    "confidence": {"type": "number"},
                    "reasoning": {"type": "string"},
                    "action": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": [
                    "headline",
                    "source",
                    "url",
                    "affected_assets",
                    "asset_type",
                    "sentiment",
                    "confidence",
                    "reasoning",
                    "action",
                    "category",
                ],
            },
        },
        "tweets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "author": {"type": "string"},
                    "text": {"type": "string"},
                    "relevance": {"type": "string"},
                },
                "required": ["author", "text", "relevance"],
            },
        },
        "disclaimer": {"type": "string"},
    },
    "required": [
        "date",
        "generated_at",
        "market_pulse",
        "insights",
        "tweets",
        "disclaimer",
    ],
}


class GeminiAnalyzer:
    """Analyse collected news via Google Gemini."""

    def __init__(self) -> None:
        if not GEMINI_API_KEY:
            raise EnvironmentError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please set it before running the analyzer."
            )
        self._client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info(
            "GeminiAnalyzer initialised (model=%s, fallbacks=%s)",
            GEMINI_MODEL,
            _FALLBACK_MODELS or "none",
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def analyze(
        self,
        news_items: list[NewsItem],
        tweets: list[NewsItem],
    ) -> dict[str, Any]:
        """Run the analysis and return the structured result."""
        logger.info(
            "Starting analysis: %d news items, %d tweets",
            len(news_items),
            len(tweets),
        )

        if not news_items and not tweets:
            logger.warning("No items to analyse — returning empty result")
            return self._empty_result()

        raw = self._call_gemini(news_items, tweets)

        # Ensure top-level metadata is accurate
        now = get_ist_now()
        raw["date"] = now.strftime("%Y-%m-%d")
        raw["generated_at"] = format_ist_datetime(now)

        # Compute market pulse from insights
        raw["market_pulse"] = self._compute_pulse(raw.get("insights", []))

        logger.info(
            "Analysis complete: %d insights, pulse=%s",
            len(raw.get("insights", [])),
            raw["market_pulse"],
        )
        return raw

    # ------------------------------------------------------------------
    # Gemini call (retry + model fallback)
    # ------------------------------------------------------------------
    def _call_gemini(
        self,
        news_items: list[NewsItem],
        tweets: list[NewsItem],
    ) -> dict[str, Any]:
        """Build the prompt and call Gemini, returning parsed JSON.

        For each model in ``[GEMINI_MODEL, *fallbacks]`` retry transient
        failures with exponential back-off before moving to the next model.
        """
        user_prompt = _TRIAGE_USER_PROMPT.format(
            max_insights=MAX_INSIGHTS,
            news_block=self._format_news_block(news_items),
            tweet_block=self._format_tweet_block(tweets),
        )

        last_exc: Exception | None = None

        for model in [GEMINI_MODEL, *_FALLBACK_MODELS]:
            gen_config = self._build_config(model)

            for attempt in range(1, _ATTEMPTS_PER_MODEL + 1):
                try:
                    response = self._client.models.generate_content(
                        model=model,
                        contents=user_prompt,
                        config=gen_config,
                    )
                    text = response.text
                    if not text:
                        raise ValueError("Gemini returned empty response")

                    parsed = json.loads(text)
                    logger.info("Gemini call succeeded with model=%s", model)
                    return parsed  # type: ignore[no-any-return]

                except genai_errors.APIError as exc:
                    last_exc = exc
                    if exc.code not in _RETRYABLE_STATUS_CODES:
                        # Bad request / auth / not-found: retrying won't help
                        # for this model. If it's a model-specific problem
                        # (e.g. 404 unknown model) try the next one.
                        logger.error(
                            "Model %s returned non-retryable error %s: %s",
                            model,
                            exc.code,
                            exc,
                        )
                        break
                    self._sleep_before_retry(model, attempt, exc.code)

                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    last_exc = exc
                    self._sleep_before_retry(model, attempt, type(exc).__name__)

                except (json.JSONDecodeError, ValueError) as exc:
                    # Empty / truncated / malformed output — worth a retry
                    last_exc = exc
                    logger.warning(
                        "Model %s returned unusable output (%s)", model, exc
                    )
                    self._sleep_before_retry(model, attempt, "bad output")

            logger.warning("Model %s exhausted — trying next fallback", model)

        logger.error("All Gemini models failed")
        assert last_exc is not None
        raise last_exc

    @staticmethod
    def _build_config(model: str) -> types.GenerateContentConfig:
        """Per-model generation config."""
        kwargs: dict[str, Any] = {
            "system_instruction": _SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": _RESPONSE_SCHEMA,
            "temperature": 0.3,
            "max_output_tokens": 8192,  # 4096 can truncate the JSON
            "http_options": types.HttpOptions(timeout=_REQUEST_TIMEOUT_MS),
        }
        # Thinking tokens count against max_output_tokens. Disable them on
        # 2.5 Flash-family models (2.5 Pro can't disable thinking; 2.0 has none).
        if "2.5" in model and "pro" not in model:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        return types.GenerateContentConfig(**kwargs)

    @staticmethod
    def _sleep_before_retry(model: str, attempt: int, reason: Any) -> None:
        if attempt >= _ATTEMPTS_PER_MODEL:
            return  # no point sleeping — we're moving on
        delay = _BASE_DELAY_SECONDS * (2 ** (attempt - 1))  # 5s, 10s
        logger.warning(
            "%s attempt %d/%d failed (%s). Retrying in %.0fs …",
            model,
            attempt,
            _ATTEMPTS_PER_MODEL,
            reason,
            delay,
        )
        time.sleep(delay)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _format_news_block(items: list[NewsItem]) -> str:
        if not items:
            return "(no news items collected)"
        lines: list[str] = []
        for i, item in enumerate(items, 1):
            lines.append(
                f"{i}. [{item.source}] {item.title}\n"
                f"   URL: {item.url}\n"
                f"   Summary: {item.summary[:200]}\n"
                f"   Tags: {', '.join(item.tags)}\n"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_tweet_block(tweets: list[NewsItem]) -> str:
        if not tweets:
            return "(no tweets collected)"
        lines: list[str] = []
        for i, tw in enumerate(tweets, 1):
            lines.append(
                f"{i}. {tw.source}: {tw.title}\n"
                f"   URL: {tw.url}\n"
            )
        return "\n".join(lines)

    @staticmethod
    def _compute_pulse(insights: list[dict[str, Any]]) -> dict[str, int]:
        pulse = {"bullish": 0, "bearish": 0, "neutral": 0}
        for ins in insights:
            sentiment = ins.get("sentiment", "neutral").lower()
            if sentiment in pulse:
                pulse[sentiment] += 1
            else:
                pulse["neutral"] += 1
        return pulse

    @staticmethod
    def _empty_result() -> dict[str, Any]:
        now = get_ist_now()
        return {
            "date": now.strftime("%Y-%m-%d"),
            "generated_at": format_ist_datetime(now),
            "market_pulse": {"bullish": 0, "bearish": 0, "neutral": 0},
            "insights": [],
            "tweets": [],
            "disclaimer": (
                "This is AI-generated analysis for informational purposes only. "
                "Not financial advice. Do your own research before investing."
            ),
        }