import csv
import sys
from pathlib import Path

from churn_evidence.cli import main
from churn_evidence.models import parse_time

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "acme_exports"


def run(tmp_path, as_of):
    out = tmp_path / as_of.replace(":", "-")
    argv = sys.argv
    sys.argv = ["churn-evidence", "--input", str(EXAMPLES), "--output", str(out), "--as-of", as_of]
    try:
        main()
    finally:
        sys.argv = argv
    with (out / "risk_queue.csv").open(newline="") as handle:
        return {row["account_id"]: row for row in csv.DictReader(handle)}


def test_timestamps_without_offset_are_utc():
    assert parse_time("2026-09-17T00:00:00") == parse_time("2026-09-17T00:00:00Z")
    assert parse_time("2026-09-17") == parse_time("2026-09-17T00:00:00+00:00")


def test_date_only_as_of_runs(tmp_path):
    rows = run(tmp_path, "2026-09-17")
    assert rows == run(tmp_path, "2026-09-17T00:00:00+00:00")


def test_past_as_of_excludes_later_evidence(tmp_path):
    # Juniper's seat removal, support thread, downgrade, and survey all land on Sep 15-16.
    rows = run(tmp_path, "2026-09-14T00:00:00+00:00")
    assert rows["acc_003"]["risk_score"] == "0"
    assert rows["acc_003"]["risk_band"] == "healthy"
    assert run(tmp_path, "2026-09-17T00:00:00+00:00")["acc_003"]["risk_band"] == "critical"
