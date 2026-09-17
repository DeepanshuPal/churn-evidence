from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .models import Account, Evidence, parse_time


def rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


def require(row: dict[str, str], keys: tuple[str, ...], filename: str) -> None:
    missing = [key for key in keys if not row.get(key, "").strip()]
    if missing:
        raise ValueError(f"{filename}: missing required values: {', '.join(missing)}")


def load_accounts(path: Path) -> dict[str, Account]:
    result: dict[str, Account] = {}
    for row in rows(path):
        require(row, ("account_id", "name"), path.name)
        result[row["account_id"]] = Account(
            account_id=row["account_id"],
            name=row["name"],
            plan=row.get("plan", "unknown") or "unknown",
            mrr=float(row.get("mrr", "0") or 0),
        )
    return result


def add_product_events(accounts: dict[str, Account], path: Path) -> None:
    """Expected PostHog-style export: account_id,event,occurred_at,properties,reference."""
    negative = {
        "activation_stalled": 24,
        "usage_drop": 28,
        "integration_failed": 18,
        "inactive_14d": 32,
        "seat_removed": 20,
    }
    positive = {"activated": -18, "power_feature_used": -10, "seat_added": -8}
    for row in rows(path):
        require(row, ("account_id", "event", "occurred_at"), path.name)
        if row["account_id"] not in accounts:
            continue
        event = row["event"]
        weight = negative.get(event, positive.get(event, 0))
        if not weight:
            continue
        details = row.get("properties", "").strip()
        summary = event.replace("_", " ") + (f": {details}" if details else "")
        accounts[row["account_id"]].evidence.append(Evidence(
            source="product", occurred_at=parse_time(row["occurred_at"]), kind=event,
            summary=summary, weight=weight,
            reference=row.get("reference", "") or f"product:{event}",
        ))


def add_support(accounts: dict[str, Account], path: Path) -> None:
    """Expected Chatwoot-style export: account_id,conversation_id,occurred_at,topic,sentiment,status,excerpt."""
    topic_weight = {"bug": 18, "missing_feature": 14, "billing": 12, "migration": 20, "performance": 16}
    sentiment_weight = {"negative": 12, "frustrated": 18, "neutral": 2, "positive": -8}
    for row in rows(path):
        require(row, ("account_id", "conversation_id", "occurred_at", "topic"), path.name)
        if row["account_id"] not in accounts:
            continue
        weight = topic_weight.get(row["topic"], 6) + sentiment_weight.get(row.get("sentiment", ""), 0)
        if row.get("status") == "unresolved":
            weight += 10
        excerpt = row.get("excerpt", "").strip()
        summary = f'{row["topic"].replace("_", " ")} support thread' + (f': "{excerpt}"' if excerpt else "")
        accounts[row["account_id"]].evidence.append(Evidence(
            source="support", occurred_at=parse_time(row["occurred_at"]), kind=row["topic"],
            summary=summary, weight=weight,
            reference=row.get("reference", "") or f'conversation:{row["conversation_id"]}',
        ))


def add_billing(accounts: dict[str, Account], path: Path) -> None:
    """Expected Kill Bill-style export: account_id,event,occurred_at,amount,reference."""
    weights = {"payment_failed": 28, "downgrade_requested": 35, "cancel_scheduled": 55,
               "discount_requested": 14, "payment_recovered": -24, "upgrade": -24}
    for row in rows(path):
        require(row, ("account_id", "event", "occurred_at"), path.name)
        if row["account_id"] not in accounts or row["event"] not in weights:
            continue
        amount = row.get("amount", "").strip()
        summary = row["event"].replace("_", " ") + (f" (${amount})" if amount else "")
        accounts[row["account_id"]].evidence.append(Evidence(
            source="billing", occurred_at=parse_time(row["occurred_at"]), kind=row["event"],
            summary=summary, weight=weights[row["event"]],
            reference=row.get("reference", "") or f'billing:{row["event"]}',
        ))


def add_surveys(accounts: dict[str, Account], path: Path) -> None:
    """Expected Formbricks-style export: account_id,response_id,occurred_at,score,reason,reference."""
    for row in rows(path):
        require(row, ("account_id", "response_id", "occurred_at", "score"), path.name)
        if row["account_id"] not in accounts:
            continue
        score = int(row["score"])
        weight = 30 if score <= 4 else 16 if score <= 6 else -14 if score >= 9 else 0
        if not weight:
            continue
        reason = row.get("reason", "").strip()
        accounts[row["account_id"]].evidence.append(Evidence(
            source="survey", occurred_at=parse_time(row["occurred_at"]), kind="survey_score",
            summary=f"survey score {score}/10" + (f': "{reason}"' if reason else ""),
            weight=weight,
            reference=row.get("reference", "") or f'survey:{row["response_id"]}',
        ))
