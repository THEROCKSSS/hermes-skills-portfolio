---
name: http-api-tester
description: "Test HTTP APIs from the command line — agent + this skill = user gets quick API verification without Postman."
version: 1.0.0
---

# http-api-tester

Test HTTP APIs quickly from the command line or Python. The agent makes requests, checks responses, and reports results — no Postman or GUI needed.

## When to Use

- The user wants to test an API endpoint quickly.
- The user is debugging an API and needs to make requests.
- The user wants to verify an API is working after deployment.
- The user says "test this API", "check this endpoint", or "is my API working".

## Quick Tests with curl

```bash
# GET request
curl -s -w "\n%{http_code}" https://api.example.com/users

# GET with headers
curl -s -H "Authorization: Bearer TOKEN" https://api.example.com/users

# POST with JSON body
curl -s -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}'

# Check response time
curl -s -o /dev/null -w "%{time_total}s" https://api.example.com/users

# Check status code only
curl -s -o /dev/null -w "%{http_code}" https://api.example.com/health
```

## Python Testing

```python
import requests
import json
from datetime import datetime

def test_endpoint(method, url, headers=None, body=None, expected_status=200):
    """Test an API endpoint and return a structured result."""
    start = datetime.now()
    try:
        resp = requests.request(
            method, url,
            headers=headers or {},
            json=body if body else None,
            timeout=30
        )
        elapsed = (datetime.now() - start).total_seconds()

        result = {
            "url": url,
            "method": method,
            "status": resp.status_code,
            "expected": expected_status,
            "passed": resp.status_code == expected_status,
            "time_ms": round(elapsed * 1000, 2),
            "headers": dict(resp.headers),
        }

        # Parse response body
        try:
            result["body"] = resp.json()
        except:
            result["body"] = resp.text[:500]

        return result
    except requests.exceptions.RequestException as e:
        return {
            "url": url,
            "method": method,
            "error": str(e),
            "passed": False
        }
```

## Batch Testing

```python
def run_test_suite(tests: list) -> list:
    """Run a suite of API tests."""
    results = []
    for test in tests:
        result = test_endpoint(
            method=test.get("method", "GET"),
            url=test["url"],
            headers=test.get("headers"),
            body=test.get("body"),
            expected_status=test.get("expected_status", 200)
        )
        result["name"] = test.get("name", test["url"])
        results.append(result)
    return results

# Example test suite
tests = [
    {"name": "Health check", "url": "https://api.example.com/health", "expected_status": 200},
    {"name": "Get users", "url": "https://api.example.com/users", "expected_status": 200},
    {"name": "Create user", "method": "POST", "url": "https://api.example.com/users",
     "body": {"name": "Test"}, "expected_status": 201},
    {"name": "Unauthorized", "url": "https://api.example.com/admin", "expected_status": 401},
]

results = run_test_suite(tests)
for r in results:
    status = "PASS" if r["passed"] else "FAIL"
    print(f"{status}: {r['name']} — {r.get('status', 'error')}")
```

## Authentication Helpers

```python
def with_auth(token: str) -> dict:
    """Generate Authorization header for Bearer token."""
    return {"Authorization": f"Bearer {token}"}

def with_basic_auth(user: str, password: str) -> dict:
    """Generate Basic auth header."""
    import base64
    cred = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {cred}"}

def with_api_key(key: str, header: str = "X-API-Key") -> dict:
    """Generate API key header."""
    return {header: key}
```

## Response Inspection

```python
def inspect_response(url: str, method: str = "GET", headers=None):
    """Detailed response inspection."""
    resp = requests.request(method, url, headers=headers or {}, timeout=30)

    print(f"Status: {resp.status_code} {resp.reason}")
    print(f"Time: {resp.elapsed.total_seconds() * 1000:.0f}ms")
    print(f"Content-Type: {resp.headers.get('content-type', 'unknown')}")
    print(f"Content-Length: {len(resp.content)} bytes")
    print(f"\nHeaders:")
    for k, v in resp.headers.items():
        print(f"  {k}: {v}")

    try:
        json_body = resp.json()
        print(f"\nBody (JSON):")
        print(json.dumps(json_body, indent=2)[:1000])
    except:
        print(f"\nBody (text):")
        print(resp.text[:500])
```

## Workflow

1. Identify the endpoint to test
2. Choose method (GET, POST, PUT, DELETE)
3. Add auth headers if needed
4. Make the request
5. Check status code and response body
6. Report pass/fail with timing

## Pitfalls

- **HTTPS certificate errors** — Self-signed certs fail by default. Use `verify=False` for testing (not production): `requests.get(url, verify=False)`.
- **Timeout** — Default timeout is 30s. For slow APIs, increase it. For health checks, use 5s so you know quickly if something is wrong.
- **Rate limiting** — Rapid requests may hit rate limits. Add `time.sleep(1)` between requests if testing the same endpoint repeatedly.
- **Response parsing** — Not all APIs return JSON. Check `content-type` header before calling `.json()`. Fall back to `.text` for non-JSON responses.
- **Following redirects** — `requests` follows redirects by default. Use `allow_redirects=False` if you want to see the 3xx response itself.
- **Sensitive headers** — Don't log auth headers in test output. Strip them before printing or storing results.
