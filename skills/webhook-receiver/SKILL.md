---
name: webhook-receiver
description: Build, deploy, and secure an HTTP webhook endpoint that receives and processes inbound webhooks from external services (Stripe, GitHub, Slack, Shopify, CI, etc.). Covers endpoint creation, HMAC signature verification, payload handling, idempotency, and response contracts.
version: 1.0.0
---

# webhook-receiver

Turn any Hermes-managed host into a trustworthy webhook ingestion point. This
skill gives you a production-ready pattern for receiving HTTP POSTs from external
services, verifying they really came from the sender, parsing the payload safely,
and returning the status code the sender expects — without dropping events under
load or leaking secrets in logs.

## When to Use

Use this skill when:

- An external provider (payments, git host, CI, SaaS) needs to **push** events to
  you via an HTTPS callback instead of you polling their API.
- You need to react to events in (near) real time: `payment.succeeded`,
  `push.created`, `issue.opened`, `order.fulfilled`, etc.
- You want a single, auditable receive → verify → process → respond pipeline.
- The integration must be replay-safe (a retried delivery must not double-fire a
  side effect).

Do **not** use this skill for: outbound API calls (that's a normal HTTP client),
long-polling/streaming consumers (use the provider's SDK), or receiving files
larger than a few MB (use signed upload URLs instead).

## Architecture

```
   External Sender                Your Endpoint                    Your System
┌──────────────┐   HTTPS POST   ┌──────────────────┐   enqueue/    ┌──────────────┐
│ Stripe/GitHub│ ─────────────▶ │  /webhooks/<src> │ ───────────▶ │  handler /
│  (signs body)│  body + HMAC   │  1. verify sig   │   async job   │  DB / action │
└──────────────┘  header        │  2. parse JSON    │               └──────────────┘
                               │  3. idempotent   │
                               │  4. respond 2xx  │
                               └──────────────────┘
```

Core principles:

- **Verify before you trust.** Reject any request whose signature does not match
  before parsing or acting on the body.
- **Return fast.** Do the minimum in the request thread (verify + enqueue), then
  process asynchronously. A slow handler makes the sender retry and floods you.
- **Be idempotent.** Senders often retry. Use the event ID + a dedup store so a
  redelivered event runs its side effect at most once.
- **Separate routes per source.** `/webhooks/stripe`, `/webhooks/github` — each
  source has its own secret and verification scheme.

## Workflow

### 1. Create the endpoint

Expose a single POST route per source behind TLS. Keep it thin:

```python
from flask import Flask, request, abort
import hmac, hashlib, json

app = Flask(__name__)

@app.post("/webhooks/stripe")
def stripe_webhook():
    payload = request.get_data()          # raw bytes — needed for HMAC
    sig = request.headers.get("Stripe-Signature", "")
    if not verify_stripe(payload, sig):
        abort(400)
    event = json.loads(payload)
    handle_event(event)                   # enqueue, don't block
    return "", 200
```

### 2. Validate signatures

Never act on an unverified body. Compute HMAC-SHA256 over the **raw** bytes with
your shared secret and compare against the sender's header using a constant-time
compare. See [Signature Verification](#signature-verification).

### 3. Process the payload

- Parse defensively: wrap `json.loads` in try/except; reject non-JSON with 400.
- Extract the event type and a stable event ID.
- Check the dedup store; if already processed, return 200 immediately.
- Otherwise enqueue for async processing and record the event ID.

```python
def handle_event(event):
    event_id = event.get("id")
    if event_id and seen(event_id):
        return
    queue.put(event)                      # e.g. Redis/RQ, SQS, a worker
    mark_seen(event_id)
```

### 4. Respond

Send the smallest correct response:

- **200 / 204** — accepted. Sender stops retrying.
- **400** — malformed or bad signature. (Most senders will not retry 4xx.)
- **500** — only on genuine internal failure; senders will retry.
- Keep the body empty or a tiny JSON ack. Do not echo the payload back.
- Target a p95 response under ~1s; offload heavy work to the worker.

## Signature Verification

Senders use HMAC. The exact header/algorithm varies by provider:

| Provider  | Header                | Scheme                                              |
|-----------|-----------------------|----------------------------------------------------|
| Stripe    | `Stripe-Signature`    | `t=<ts>,v1=<HMAC-SHA256(raw, secret)>`             |
| GitHub    | `X-Hub-Signature-256` | `sha256=<HMAC-SHA256(raw, secret)>`                |
| Slack     | `X-Slack-Signature`   | `v0=<HMAC-SHA256("v0:"+ts+":"+raw, secret)>`       |

Generic verifier:

```python
def constant_time_equal(a, b):
    return hmac.compare_digest(a, b)

def verify(payload: bytes, header_sig: str, secret: str, prefix: str = "sha256="):
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    provided = header_sig[len(prefix):] if header_sig.startswith(prefix) else header_sig
    return constant_time_equal(expected, provided)
```

Rules:
- Use `hmac.compare_digest`, never `==` (avoids timing leaks).
- Verify over **raw bytes**, not the re-serialized JSON (whitespace/key order
  changes the digest).
- For timestamped schemes (Stripe, Slack), reject if `|now - ts| > 300s` to
  prevent replay attacks.
- Store the secret in an env var / secret manager. Never in source control.

## Payload Handling

- **Define a schema.** Map known event types to handlers; ignore unknown types
  with 200 (senders add new types without warning).
- **Validate shape, not just presence.** Use a lightweight validator (pydantic,
  jsonschema) so a malformed event fails loudly rather than crashing mid-flight.
- **Don't trust types.** A `price` field could arrive as string; coerce
  explicitly.
- **Log minimally.** Record `event_id`, `type`, and `source` — never the full
  body or headers (they may contain PII or secrets).
- **Backpressure.** If the queue is full, return 503 so the sender retries later
  instead of losing the event.

## Error Handling

- **Bad signature / malformed JSON** → 400, no retry expected. Log as security
  event.
- **Unknown event type** → 200, drop silently (or to a dead-letter log).
- **Transient processing failure** → raise so the worker retries with backoff.
  Keep the HTTP layer returning 200 once the event is durably enqueued.
- **Duplicate delivery** → detected via dedup store, return 200, no side effect.
- **Dead letters.** After N retries, move to a DLQ for human inspection rather
  than dropping.
- Never let an unhandled exception bubble into a 500 for a *verified* event that
  you already accepted — that triggers wasteful redelivery.

## Pitfalls

- **Verifying the wrong bytes.** Re-serializing JSON before HMAC is the #1 bug.
  Always digest `request.get_data()`.
- **Using `==` for signatures.** Timing attacks are real; use `compare_digest`.
- **Blocking in the request handler.** Slow work → sender timeout → retry storm.
  Enqueue and return.
- **Non-idempotent handlers.** Retries double-charge or double-post. Always
  dedup on event ID.
- **Secret in git / logs.** Rotate immediately if leaked; use a secret manager.
- **Ignoring replay windows.** Without timestamp checks, an old captured request
  can be replayed later. Enforce `|now - ts|` limits.
- **Returning 500 for ignorable events.** Unknown types should be 200, not errors.
- **No HTTPS / no source routing.** Plaintext + one shared route makes rotation
  and auditing impossible.
- **Accepting huge bodies.** Cap `Content-Length` (e.g. 1–5 MB) before reading.

## Verification Checklist

- [ ] Endpoint is HTTPS-only and returns 200 for a valid signed test event.
- [ ] Invalid signature returns 400 and is logged as a security event.
- [ ] Same event ID delivered twice runs the side effect once.
- [ ] Response time < 1s even when processing is slow (offloaded to worker).
- [ ] Secret is in a secret manager, absent from source and logs.
- [ ] Replay with a stale timestamp is rejected.
