# api-test-suite

Turn an API into a runnable test suite — contract tests, integration tests, and CI config — generated from an OpenAPI spec, a Postman collection, or an existing API codebase.

## What it does

The agent reads your API's source of truth (a spec file or the route code itself) and writes a test package you can run locally and wire into CI. It covers the happy path, the obvious error cases (auth, validation, not-found), and the edge cases people forget (empty bodies, malformed input, rate limits). Then it runs the suite and tells you what passed, what failed, and whether the failure is a bug in your API or a wrong expectation in the test.

This is a generator, not a hosted runner. The output is real files in your repo that you own and can edit.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/api-test-suite/SKILL.md
```

## Inputs

The skill accepts any one of these as the source of truth:

| Input | Example | What it drives |
|---|---|---|
| OpenAPI / Swagger spec | `openapi.yaml`, `swagger.json` | Endpoint list, shapes, response codes |
| Postman collection | `collection.json` | Endpoint list, example requests |
| API codebase | FastAPI, Express, Flask, Nest | Route scans, auth schemes |

If you have a spec, that wins — it is the contract. If you only have code, the agent scans route definitions and infers auth and shapes, then asks you to confirm anything ambiguous.

## What you get

```
tests/
  conftest.py            # pytest fixtures: base_url, auth_headers, cleanup
  contract/
    test_contract.py     # schema-conformance checks (spec-driven)
    test_shapes.py
  integration/
    test_orders.py       # real HTTP happy / error / edge cases
helpers/
  http.py                # shared client, base URL from env
  auth.py                # test-token minting
openapi.json             # spec under test (if you provided one)
pytest.ini
```

Node/TS projects get the same shape with `vitest.config.ts` and `*.test.ts` / `*.spec.ts` files, plus a `helpers/http.ts` and `helpers/auth.ts`.

## Contract tests

Contract tests assert the live API's responses conform to the published schema. They catch drift between what you documented and what you shipped.

```python
# tests/contract/test_shapes.py
import json
import httpx
from jsonschema import Draft202012Validator

spec = json.load(open("openapi.json"))
schema = (
    spec["paths"]["/markets"]["get"]["responses"]["200"]["content"]
    ["application/json"]["schema"]
)

def test_markets_shape(base_url):
    r = httpx.get(f"{base_url}/markets?limit=10")
    assert r.status_code == 200
    Draft202012Validator(schema).validate(r.json())
```

The rule that makes this worth having: the expectation is read from the spec, not copied into the test. A hardcoded copy silently rots; a spec-derived check fails the moment the API and the contract disagree, which is the whole point.

For deeper coverage, `schemathesis` generates requests from the spec and validates every response against it automatically:

```python
import schemathesis
schema = schemathesis.from_uri("http://localhost:8000/openapi.json")

@schema.parametrize()
def test_api_contract(case, base_url):
    response = case.call(base_url)
    case.validate_response(response)
```

## Integration tests

Integration tests exercise real HTTP behavior against a running server (or an in-process app) with auth, test data, and cleanup. Fixtures create their own data and tear it down, so tests stay isolated.

```python
# tests/integration/test_orders.py
import pytest, httpx

@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {mint_test_token(scopes=['orders:write'])}"}

@pytest.fixture
def created_order(base_url, auth_headers):
    r = httpx.post(f"{base_url}/orders", json={"item": "widget", "qty": 1},
                   headers=auth_headers)
    assert r.status_code == 201
    yield r.json()["id"]
    httpx.delete(f"{base_url}/orders/{r.json()['id']}", headers=auth_headers)

def test_create_order_happy(base_url, auth_headers, created_order):
    assert isinstance(created_order, str)

def test_create_order_requires_auth(base_url):
    r = httpx.post(f"{base_url}/orders", json={"item": "widget"})
    assert r.status_code == 401

def test_create_order_empty_body(base_url, auth_headers):
    r = httpx.post(f"{base_url}/orders", json={}, headers=auth_headers)
    assert r.status_code == 400
```

Node/TS, in-process with `supertest`:

```ts
// tests/integration/orders.test.ts
import request from 'supertest'
import { app } from '../../src/app'
import { testToken } from '../helpers/auth'

describe('POST /orders', () => {
  it('creates an order with valid auth', async () => {
    const r = await request(app)
      .post('/orders')
      .set('Authorization', `Bearer ${testToken()}`)
      .send({ item: 'widget', qty: 1 })
    expect(r.status).toBe(201)
  })

  it('rejects missing auth', async () => {
    const r = await request(app).post('/orders').send({ item: 'widget' })
    expect(r.status).toBe(401)
  })
})
```

## Test runner setup

**Python** — `pip install pytest httpx schemathesis`, then `pytest.ini`:

```ini
[pytest]
testpaths = tests
addopts = -q --tb=short
env =
  BASE_URL=http://localhost:8000
```

**Node/TS** — `npm i -D vitest supertest`, then `vitest.config.ts`:

```ts
import { defineConfig } from 'vitest/config'
export default defineConfig({
  test: { globals: true, environment: 'node',
          include: ['tests/**/*.test.ts', 'tests/**/*.spec.ts'] },
})
```

## CI integration

Run the suite against a service the pipeline spins up. This YAML works in both GitHub Actions and Forgejo Actions:

```yaml
name: api-tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      api:
        image: ghcr.io/your-org/your-api:ci
        ports: ["8000:8000"]
        options: >-
          --health-cmd "curl -f http://localhost:8000/health"
          --health-interval 10s --health-timeout 5s --health-retries 5
    env:
      BASE_URL: http://localhost:8000
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install pytest httpx schemathesis
      - run: pytest tests/ --junitxml=report.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: api-test-report, path: report.xml }
```

Swap the setup/run steps for `actions/setup-node` and `npx vitest run` on a Node project.

## Coverage matrix

The agent generates at least one case per endpoint from each row:

| Category | Case | Expected |
|---|---|---|
| Happy path | Valid request, valid auth | 2xx, shape matches spec |
| Auth | Missing / invalid token | 401 / 403 |
| Validation | Missing required field, bad type | 400, documented error shape |
| Not found | Unknown ID | 404 |
| Edge | Empty body, malformed JSON, oversized input | 400 / 413 |
| Edge | Pagination bounds (`limit=0`, `limit=1000`) | 200 or 422, sane clamping |
| Edge | Rate limit (burst) | 429 with retry header |

## Honest limitations

- The suite documents observed behavior. For ambiguous endpoints the agent confirms intent with you rather than guessing the "right" contract.
- Contract tests check shape and codes; they do not prove business logic correctness. Pair them with a few hand-written behavior tests for your critical paths.
- Generated fixtures use a test tenant and short-lived tokens. You must wire real secret injection (`BASE_URL`, token minting) for your environment — the skill scaffolds it, it does not know your auth system.
- Rate-limited APIs will 429 under load; the skill serializes contract runs and raises the limit for the test tenant instead of masking failures.

## Part of

[Hermes Skills Portfolio](https://github.com/THEROCKSSS/hermes-skills-portfolio) — empowering skills for the Hermes agent.
