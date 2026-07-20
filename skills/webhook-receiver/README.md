# webhook-receiver

A public Hermes skill for building **secure, reliable inbound webhook endpoints**.

Receive events from Stripe, GitHub, Slack, Shopify, CI systems, and any other
provider that pushes via HTTPS — verify they really came from the sender, process
them safely, and respond with the exact status code the sender expects.

> Agent + skill = a working webhook endpoint, not a tutorial.

## Why this exists

Most webhook integrations break in the same three places: the signature check is
wrong, retries cause double-processing, or a slow handler triggers a retry
storm. `webhook-receiver` encodes the verify → parse → dedupe → enqueue →
respond pipeline that fixes all three by default.

## What you get

- **Thin, TLS-only endpoints** — one POST route per source, returning in <1s.
- **HMAC signature verification** — constant-time compare over raw bytes, with
  per-provider header schemes (Stripe, GitHub, Slack) and replay-window checks.
- **Idempotent processing** — dedup on event ID so retried deliveries never
  double-fire a side effect.
- **Safe payload handling** — schema validation, minimal logging (no PII/secrets
  in logs), and backpressure via 503.
- **Clear error contract** — 200 accept, 400 reject, 500 retry; unknown event
  types dropped cleanly.

## Install

Point Hermes at the skill manifest:

```
https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/webhook-receiver/SKILL.md
```

Or clone the portfolio and load `skills/webhook-receiver` locally.

## Quick start

```python
import hmac, hashlib, json
from flask import Flask, request, abort

app = Flask(__name__)
SECRET = "your-secret-from-secret-manager"   # never hardcode

@app.post("/webhooks/stripe")
def stripe_webhook():
    payload = request.get_data()             # raw bytes for HMAC
    sig = request.headers.get("Stripe-Signature", "")
    expected = hmac.new(SECRET.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig.split("v1=")[-1]):
        abort(400)                           # verify before trust
    event = json.loads(payload)
    handle_event(event)                      # enqueue, don't block
    return "", 200
```

See `SKILL.md` for the full workflow, signature tables, dedup patterns, and the
verification checklist.

## Author

Part of the public [Hermes Skills Portfolio](https://github.com/THEROCKSSS/hermes-skills-portfolio)
by **Monica Amano**.
