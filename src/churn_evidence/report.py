from __future__ import annotations

import csv
import json
from pathlib import Path

from .engine import Dossier


def as_dict(dossier: Dossier) -> dict:
    return {
        "account_id": dossier.account.account_id,
        "name": dossier.account.name,
        "plan": dossier.account.plan,
        "mrr": dossier.account.mrr,
        "risk_score": dossier.score,
        "risk_band": dossier.band,
        "confidence": dossier.confidence,
        "evidence": [{
            "source": item.source,
            "occurred_at": item.occurred_at.isoformat(),
            "kind": item.kind,
            "summary": item.summary,
            "weight": item.weight,
            "reference": item.reference,
        } for item in dossier.reasons],
        "plays": dossier.plays,
    }


def write_json(dossiers: list[Dossier], path: Path) -> None:
    path.write_text(json.dumps([as_dict(item) for item in dossiers], indent=2) + "\n", encoding="utf-8")


def write_csv(dossiers: list[Dossier], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["account_id", "name", "plan", "mrr", "risk_score", "risk_band", "confidence", "top_evidence", "next_play"])
        writer.writeheader()
        for item in dossiers:
            writer.writerow({
                "account_id": item.account.account_id, "name": item.account.name,
                "plan": item.account.plan, "mrr": f"{item.account.mrr:.2f}",
                "risk_score": item.score, "risk_band": item.band, "confidence": item.confidence,
                "top_evidence": item.reasons[0].summary if item.reasons else "",
                "next_play": item.plays[0] if item.plays else "",
            })


def write_markdown(dossiers: list[Dossier], path: Path) -> None:
    lines = ["# Churn evidence report", "", "Scores are explainable indicators, not predictions. Every reason links to the supplied source reference.", ""]
    for item in dossiers:
        lines += [f"## {item.account.name} - {item.score}/100 ({item.band})", "", f"Plan: `{item.account.plan}` · MRR: `${item.account.mrr:,.0f}` · Confidence: **{item.confidence}**", "", "### Evidence"]
        if item.reasons:
            for evidence in item.reasons:
                lines.append(f"- **{evidence.source}** · {evidence.occurred_at.date()} · {evidence.summary} ([source]({evidence.reference}))")
        else:
            lines.append("- No positive-risk evidence in the supplied window.")
        lines += ["", "### Suggested plays"] + [f"{index}. {play}" for index, play in enumerate(item.plays, 1)] + [""]
    path.write_text("\n".join(lines), encoding="utf-8")
