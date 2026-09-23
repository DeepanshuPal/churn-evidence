from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

from .models import Account, Evidence


@dataclass(frozen=True)
class Dossier:
    account: Account
    score: int
    band: str
    reasons: list[Evidence]
    plays: list[str]
    confidence: str


def decayed_weight(item: Evidence, as_of: datetime) -> float:
    days = max(0.0, (as_of - item.occurred_at).total_seconds() / 86400)
    return item.weight * math.pow(0.5, days / 45)


def choose_plays(reasons: list[Evidence]) -> list[str]:
    kinds = {item.kind for item in reasons}
    sources = {item.source for item in reasons}
    plays: list[str] = []
    if "cancel_scheduled" in kinds or "downgrade_requested" in kinds:
        plays.append("Open a save-plan review with the account owner before the billing change lands.")
    if kinds & {"bug", "performance", "integration_failed"}:
        plays.append("Assign one technical owner and send a dated recovery plan tied to the cited failure.")
    if kinds & {"activation_stalled", "inactive_14d", "usage_drop"}:
        plays.append("Run a focused activation reset around the last missing or abandoned workflow.")
    if "survey" in sources:
        plays.append("Close the loop on the survey reason in the next customer touch, quoting it directly.")
    if "billing" in sources and "payment_failed" in kinds:
        plays.append("Separate payment recovery from product-risk outreach so the account gets one clear ask.")
    if not plays:
        plays.append("Review the linked evidence with the account owner before choosing an intervention.")
    return plays[:3]


def build_dossier(account: Account, as_of: datetime | None = None) -> Dossier:
    as_of = as_of or datetime.now(timezone.utc)
    # Score a point-in-time snapshot: evidence recorded after as_of did not exist yet.
    known = [item for item in account.evidence if item.occurred_at <= as_of]
    weighted = sorted(((decayed_weight(item, as_of), item) for item in known), reverse=True, key=lambda x: x[0])
    score = max(0, min(100, round(sum(value for value, _ in weighted))))
    band = "critical" if score >= 70 else "high" if score >= 45 else "watch" if score >= 20 else "healthy"
    reasons = [item for value, item in weighted if value > 0][:5]
    source_count = len({item.source for item in reasons})
    confidence = "high" if source_count >= 3 else "medium" if source_count == 2 else "low"
    return Dossier(account, score, band, reasons, choose_plays(reasons), confidence)
