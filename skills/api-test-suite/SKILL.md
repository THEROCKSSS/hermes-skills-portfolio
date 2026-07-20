---
name: api-test-suite
description: "Generate a runnable API test suite — contract tests, integration tests, and CI config — from an OpenAPI spec or existing API. Agent + this skill = user gets tests that actually run."
version: 1.0.0
---

# api-test-suite

Generate a runnable API test package from an OpenAPI spec, a Postman collection, or by scanning an existing API codebase. The agent produces real, locally-runnable test files — not a hosted-run stub — covering happy path, error cases, and edge cases, then runs the suite and reports pass/fail.

## When to Use

- A new API project needs test coverage before it ships.
- The user says "write tests for these endpoints", "add contract tests", or "test my API".
- Pre-release or pre-merge verification of an HTTP API.
- You have an OpenAPI/Postman artifact and want it turned into executable tests.
- You are onboarding to an API codebase and want a safety net first.

Do not use it for browser UI flows (use a browser-test skill) or for pure unit tests of non-API logic (those belong in a unit test file, not the API suite).

## Workflow

1. **Pick the input.** One of:
   - An OpenAPI/Swagger spec (`openapi.yaml`, `swagger.json`).
   - A Postman collection (`collection.json`).
   - An API codebase (FastAPI/Express/Flask/Nest/etc.) — scan route definitions.
2. **Enumerate endpoints** with method, path, auth scheme, request shape, and response codes.
3. **Derive test cases per endpoint:**
   - Happy path — 2xx, response shape matches spec.
   - Auth missing/invalid — 401/403.
   - Validation failure — 400, with the documented error shape.
   - Not found — 404 for unknown IDs.
   - Edge cases — empty body, oversized input, malformed JSON, pagination bounds, rate limiting.
4. **Choose a runner by stack:**
   - Node/TS → `vitest` + `supertest` (in-process) or `axios` (live server).
   - Python → `pytest` + `httpx` (live server) or `fastapi.testclient` (in-process).
5. **Emit the file tree** (see Test Runner Setup).
6. **Run the suite.** Report pass/fail per file. If a test fails, decide whether it is a real bug in the API or a wrong expectation in the test — fix the API when the expectation is correct, fix the test when it is not. Never delete or weaken an assertion just to turn it green.

## Contract Tests

Contract tests assert that the live API's responses conform to the published schema. They catch drift between spec and implementation.

**From an OpenAPI spec — Python with schemathesis (property-based, hits the running server):**

```python
# tests/contract/test_contract.py
import schemathesis

schema = schemathesis.from_uri("http://localhost:8000/openapi.json")

@schema.parametrize()
def test_api_contract(case, base_url):
    # `case` is generated from the spec; this verifies the server honors it
    response = case.call(base_url)
    case.validate_response(response)
```

If schemathesis is too heavy, validate responses against a JSON Schema extracted from the spec:

```python
# tests/contract/test_shapes.py
import json
import httpx
from jsonschema import Draft202012Validator

spec = json.load(open("openapi.json"))
# pull the response schema for GET /markets -> 200
schema = spec["paths"]["/markets"]["get"]["responses"]["200"]["content"][
    "application/json"
]["schema"]

def test_markets_shape(base_url):
    r = httpx.get(f"{base_url}/markets?limit=10")
    assert r.status_code == 200
    Draft202012Validator(schema).validate(r.json())
```

**From an OpenAPI spec — Node with a lightweight assertion:**

```ts
// tests/contract/markets.spec.ts
import { expect } from 'vitest'
import { client } from '../helpers/http'

it('GET /markets 200 matches spec shape', async () => {
  const r = await client.get('/markets?limit=10')
  expect(r.status).toBe(200)
  expect(Array.isArray(r.data.data)).toBe(true)
  expect(r.data).toHaveProperty('total')
})
```

Rule: contract tests must read the schema from the artifact, not hardcode a copy that can silently rot.

## Integration Tests

Integration tests exercise real HTTP behavior against a running server (or an in-process app) with auth, test data, and cleanup.

**Python — fixtures for auth, data, cleanup (pytest):**

```python
# tests/integration/test_orders.py
import pytest, httpx

@pytest.fixture
def auth_headers():
    # mint a short-lived test token; never use a real user's credentials
    token = mint_test_token(scopes=["orders:write"])
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def created_order(base_url, auth_headers):
    r = httpx.post(f"{base_url}/orders", json={"item": "widget", "qty": 1},
                   headers=auth_headers)
    assert r.status_code == 201
    yield r.json()["id"]
    # cleanup runs even if the test fails
    httpx.delete(f"{base_url}/orders/{r.json()['id']}", headers=auth_headers)

def test_create_order_happy(base_url, auth_headers, created_order):
    assert isinstance(created_order, str)

def test_create_order_requires_auth(base_url):
    r = httpx.post(f"{base_url}/orders", json={"item": "widget"})
    assert r.status_code == 401

def test_create_order_bad_payload(base_url, auth_headers):
    r = httpx.post(f"{base_url}/orders", json={}, headers=auth_headers)
    assert r.status_code == 400
```

**Node — vitest + supertest (in-process, no separate server):**

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

  it('rejects empty body', async () => {
    const r = await request(app)
      .post('/orders')
      .set('Authorization', `Bearer ${testToken()}`)
      .send({})
    expect(r.status).toBe(400)
  })
})
```

## Test Runner Setup

Emit this layout so the suite is reproducible:

```
tests/
  conftest.py            # pytest fixtures: base_url, auth_headers, data, cleanup
  contract/
    test_contract.py     # schema-conformance checks
    test_shapes.py
  integration/
    test_orders.py       # real HTTP happy/error/edge cases
helpers/
  http.ts / http.py      # shared client, base URL from env
  auth.ts / auth.py      # test-token minting
openapi.json             # spec under test (if available)
pytest.ini / vitest.config.ts
```

**Python — `pytest.ini`:**

```ini
[pytest]
testpaths = tests
addopts = -q --tb=short
env =
  BASE_URL=http://localhost:8000
```

Install: `pip install pytest httpx schemathesis`

**Node — `vitest.config.ts`:**

```ts
import { defineConfig } from 'vitest/config'
export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.ts', 'tests/**/*.spec.ts'],
  },
})
```

Install: `npm i -D vitest supertest`

## CI Integration

Run contract + integration tests against a service spun up in the pipeline. GitHub Actions / Forgejo Actions share the same YAML:

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

For Node, swap the setup step for `actions/setup-node` and the run step for `npx vitest run`.

## Pitfalls

- **Mocking the database so tests lie.** Use a real test database or per-test transaction rollback. A test that mocks storage at the wrong boundary passes while the API is broken.
- **Hardcoding the response shape instead of reading the spec.** Contract tests must derive expectations from the OpenAPI/Postman artifact, or they drift and become noise.
- **Shared mutable state across tests.** Each test must create and clean up its own data. Seeds that depend on order will flake in CI.
- **Using a real user's token for auth.** Mint short-lived test tokens scoped to the test tenant; rotate secrets from env, never commit them.
- **Rate limiting breaking CI.** Hit the API serially in contract runs, or raise the limit for the test tenant. A 429 is a test-harness problem, not an API bug, until proven otherwise.
- **Treating generated tests as a substitute for reading the spec.** The suite documents behavior; the agent should still confirm the API's intent with the user for ambiguous endpoints.
- **Flaky network timing.** Add bounded retries only on connection errors, never on assertion failures.
