from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def parse_time(value: str) -> datetime:
    cleaned = value.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(cleaned)


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
