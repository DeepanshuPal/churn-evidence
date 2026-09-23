from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from .engine import build_dossier
from .loaders import add_billing, add_product_events, add_support, add_surveys, load_accounts
from .models import parse_time
from .report import write_csv, write_json, write_markdown


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build evidence-linked churn dossiers from local exports.")
    p.add_argument("--input", type=Path, required=True, help="Directory containing accounts.csv and optional source exports.")
    p.add_argument("--output", type=Path, default=Path("output"), help="Output directory.")
    p.add_argument("--as-of", help="ISO timestamp to score as of. Evidence after it is ignored; no offset means UTC. Defaults to now.")
    p.add_argument("--min-score", type=int, default=0, help="Only emit accounts at or above this risk score.")
    return p


def main() -> None:
    args = parser().parse_args()
    accounts_path = args.input / "accounts.csv"
    if not accounts_path.exists():
        raise SystemExit(f"Missing required file: {accounts_path}")
    accounts = load_accounts(accounts_path)
    loaders = {
        "product_events.csv": add_product_events,
        "support_conversations.csv": add_support,
        "billing_events.csv": add_billing,
        "survey_responses.csv": add_surveys,
    }
    for filename, loader in loaders.items():
        path = args.input / filename
        if path.exists():
            loader(accounts, path)
    as_of = parse_time(args.as_of) if args.as_of else datetime.now(timezone.utc)
    dossiers = sorted((build_dossier(account, as_of) for account in accounts.values()), key=lambda item: (item.score, item.account.mrr), reverse=True)
    dossiers = [item for item in dossiers if item.score >= args.min_score]
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(dossiers, args.output / "dossiers.json")
    write_csv(dossiers, args.output / "risk_queue.csv")
    write_markdown(dossiers, args.output / "report.md")
    print(f"Wrote {len(dossiers)} dossiers to {args.output}")


if __name__ == "__main__":
    main()
