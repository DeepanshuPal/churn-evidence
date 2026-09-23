from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def parse_time(value: str) -> datetime:
    """Parse an ISO 8601 timestamp; values without an offset are treated as UTC."""
    cleaned = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


@dataclass(frozen=True)
class Evidence:
    source: str
    occurred_at: datetime
    kind: str
    summary: str
    weight: int
    reference: str


@dataclass
class Account:
    account_id: str
    name: str
    plan: str = "unknown"
    mrr: float = 0.0
    evidence: list[Evidence] = field(default_factory=list)
