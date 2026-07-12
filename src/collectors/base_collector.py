"""
Base abstractions for all news / social-media collectors.

Every concrete collector inherits from ``BaseCollector`` and implements
the ``collect`` method that returns a list of ``NewsItem`` instances.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class NewsItem:
    """A single piece of news or social-media content."""

    title: str
    summary: str
    source: str
    url: str
    timestamp: str
    tags: list[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"NewsItem(title={self.title!r}, source={self.source!r})"


class BaseCollector(ABC):
    """Abstract base class that every collector must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this collector (used in logs)."""
        ...

    @abstractmethod
    def collect(self) -> list[NewsItem]:
        """Fetch and return relevant ``NewsItem`` objects."""
        ...
