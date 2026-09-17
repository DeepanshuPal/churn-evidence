from pathlib import Path

from churn_evidence.loaders import add_product_events, load_accounts


def test_unknown_accounts_are_skipped(tmp_path: Path):
    (tmp_path / "accounts.csv").write_text("account_id,name\na1,Acme\n", encoding="utf-8")
    (tmp_path / "events.csv").write_text("account_id,event,occurred_at\na2,usage_drop,2026-09-17T00:00:00+00:00\n", encoding="utf-8")
    accounts = load_accounts(tmp_path / "accounts.csv")
    add_product_events(accounts, tmp_path / "events.csv")
    assert not accounts["a1"].evidence
