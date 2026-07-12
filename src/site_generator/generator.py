"""
Site data generator.

Writes the analysis output to:
  - ``site/data/latest.json``          — always overwritten
  - ``site/data/archive/YYYY-MM-DD.json`` — daily archive
  - ``site/data/archive/index.json``   — list of available archive dates
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Base directory for generated data (relative to project root)
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_SITE_DATA_DIR = os.path.join(_PROJECT_ROOT, "web", "public", "data")
_ARCHIVE_DIR = os.path.join(_SITE_DATA_DIR, "archive")


class SiteGenerator:
    """Generate JSON data files consumed by the frontend."""

    def __init__(self, data_dir: str | None = None) -> None:
        self._data_dir = data_dir or _SITE_DATA_DIR
        self._archive_dir = os.path.join(self._data_dir, "archive")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(self, insights_data: dict[str, Any]) -> None:
        """Write *insights_data* to latest.json and the daily archive."""
        self._ensure_dirs()

        # 1. Write latest.json
        latest_path = os.path.join(self._data_dir, "latest.json")
        self._write_json(latest_path, insights_data)
        logger.info("Wrote latest data → %s", latest_path)

        # 2. Write daily archive
        date_str = insights_data.get("date", "unknown")
        archive_path = os.path.join(self._archive_dir, f"{date_str}.json")
        self._write_json(archive_path, insights_data)
        logger.info("Wrote archive → %s", archive_path)

        # 3. Update archive index
        self._update_index()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _ensure_dirs(self) -> None:
        """Create output directories if they don't exist."""
        os.makedirs(self._data_dir, exist_ok=True)
        os.makedirs(self._archive_dir, exist_ok=True)

    @staticmethod
    def _write_json(path: str, data: dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)

    def _update_index(self) -> None:
        """Scan the archive directory and write ``index.json`` with a
        sorted list of available dates."""
        dates: list[str] = []
        for filename in os.listdir(self._archive_dir):
            if filename.endswith(".json") and filename != "index.json":
                dates.append(filename.removesuffix(".json"))

        dates.sort(reverse=True)
        index_path = os.path.join(self._archive_dir, "index.json")
        self._write_json(index_path, {"dates": dates})
        logger.info(
            "Updated archive index (%d dates) → %s", len(dates), index_path
        )
