# churn-evidence

**Explainable churn triage from the customer evidence you already own.**

Churn Evidence joins product events, support conversations, billing changes, and survey responses into a ranked risk queue. Every reason links back to the supplied source record. The score is an indicator, not a black-box prediction.

It borrows the useful data shapes of [PostHog](https://github.com/posthog/posthog), [Chatwoot](https://github.com/chatwoot/chatwoot), [Kill Bill](https://github.com/killbill/killbill), and [Formbricks](https://github.com/formbricks/formbricks), then makes the cross-source workflow runnable from plain exports.

## Why this exists

Most churn tools ask you to trust a score. GTM teams still need to answer:

- What changed?
- Which customer words support the claim?
- Is this product risk, commercial risk, or both?
- What should the account owner do next?

This tool keeps those answers in one dossier and does not send customer messages.

## Demo

```bash
git clone https://github.com/DeepanshuPal/churn-evidence.git
cd churn-evidence
python -m venv .venv && source .venv/bin/activate
python -m pip install -e .

churn-evidence \
  --input examples/acme_exports \
  --output output \
  --as-of 2026-09-17T00:00:00+00:00
```

Outputs:

```text
output/
├── dossiers.json   # complete machine-readable dossiers
├── report.md       # evidence-linked account briefs
└── risk_queue.csv  # ranked queue for CRM or spreadsheet import
```

Example queue:

| account | risk | band | confidence | first move |
|---|---:|---|---|---|
| Northstar Labs | 100 | critical | high | Assign one technical owner and send a dated recovery plan. |
| Juniper Cloud | 100 | critical | high | Open a save-plan review before the billing change lands. |
| Relay Goods | 0 | healthy | low | Review evidence before choosing an intervention. |

## Input contract

`accounts.csv` is required. The other files are optional. All timestamps are ISO 8601; a timestamp without an offset is read as UTC.

`--as-of` scores a point-in-time snapshot: evidence dated after it is left out, so you can rerun a past triage from a newer export and get the queue you would have seen that day.

### `accounts.csv`

```csv
account_id,name,plan,mrr
acc_001,Northstar Labs,Growth,2400
```

### `product_events.csv`

PostHog-style fields:

```csv
account_id,event,occurred_at,properties,reference
acc_001,usage_drop,2026-09-13T10:00:00+00:00,Weekly active seats fell 42%,https://posthog.example/insight/1
```

Recognized events include `activation_stalled`, `usage_drop`, `integration_failed`, `inactive_14d`, `seat_removed`, `activated`, `power_feature_used`, and `seat_added`.

### `support_conversations.csv`

Chatwoot-style fields:

```csv
account_id,conversation_id,occurred_at,topic,sentiment,status,excerpt,reference
acc_001,c_193,2026-09-14T12:30:00+00:00,bug,frustrated,unresolved,Sync keeps failing,https://chatwoot.example/conversations/193
```

### `billing_events.csv`

Kill Bill-style fields:

```csv
account_id,event,occurred_at,amount,reference
acc_001,payment_failed,2026-09-15T06:00:00+00:00,2400,https://billing.example/invoices/89
```

### `survey_responses.csv`

Formbricks-style fields:

```csv
account_id,response_id,occurred_at,score,reason,reference
acc_001,r_99,2026-09-16T15:00:00+00:00,3,Reliability is blocking rollout,https://formbricks.example/responses/r_99
```

## Scoring model

- Source events have documented, deterministic weights.
- Risk decays with a 45-day half-life.
- Positive signals such as activation, upgrades, and payment recovery lower the score.
- Scores are clamped to 0-100.
- Confidence reflects cross-source corroboration, not model certainty.
- Suggested plays are rule-based and tied to the evidence types present.

The scoring code is in [`engine.py`](src/churn_evidence/engine.py). Change the weights and plays to match your motion.

## Cost and data handling

- **Default cost:** $0
- **Runtime:** local Python and the standard library
- **Database:** none required
- **LLM:** none required
- **Telemetry:** none
- **Network calls:** none

Exports stay on the machine running the command. API adapters can be added without changing the dossier engine.

## Roadmap

- Direct adapters for self-hosted PostHog, Chatwoot, Kill Bill, and Formbricks
- Configurable scoring rules in YAML
- Cohort baselines so usage drops are relative to each account
- Optional local-model summaries, kept separate from the risk calculation
- CRM write-back behind an explicit human approval queue

## Development

```bash
python -m pip install -e . pytest
pytest -q
```

## License

MIT
