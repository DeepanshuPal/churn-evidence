from datetime import datetime, timezone

from churn_evidence.engine import build_dossier
from churn_evidence.models import Account, Evidence

NOW = datetime(2026, 9, 17, tzinfo=timezone.utc)


def evidence(source: str, kind: str, weight: int) -> Evidence:
    return Evidence(source, NOW, kind, kind, weight, f"https://example.test/{kind}")


def test_multi_source_risk_is_ranked_and_explained():
    account = Account("a1", "Acme", "growth", 900, [
        evidence("billing", "cancel_scheduled", 55),
        evidence("support", "bug", 30),
        evidence("survey", "survey_score", 30),
    ])
    dossier = build_dossier(account, NOW)
    assert dossier.score == 100
    assert dossier.band == "critical"
    assert dossier.confidence == "high"
    assert dossier.reasons[0].kind == "cancel_scheduled"
    assert len(dossier.plays) >= 2


def test_positive_signals_reduce_risk():
    account = Account("a2", "Beta", evidence=[
        evidence("product", "usage_drop", 28),
        evidence("billing", "upgrade", -24),
    ])
    dossier = build_dossier(account, NOW)
    assert dossier.score == 4
    assert dossier.band == "healthy"


def test_old_evidence_decays():
    old = Evidence("support", datetime(2026, 6, 19, tzinfo=timezone.utc), "bug", "bug", 40, "x")
    dossier = build_dossier(Account("a3", "Gamma", evidence=[old]), NOW)
    assert dossier.score == 10


def test_evidence_after_as_of_is_ignored():
    future = Evidence("billing", datetime(2026, 9, 18, tzinfo=timezone.utc), "cancel_scheduled",
                      "cancel scheduled", 55, "billing:cancel")
    past = evidence("support", "bug", 18)
    dossier = build_dossier(Account("a4", "Delta", evidence=[future, past]), NOW)
    assert dossier.score == 18
    assert [item.kind for item in dossier.reasons] == ["bug"]
    assert all("save-plan" not in play for play in dossier.plays)
