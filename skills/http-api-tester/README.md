# http-api-tester

Test HTTP APIs from the command line — quick verification without Postman or a GUI.

## What it does

The agent makes HTTP requests to your API endpoints, checks the response status and body, and reports pass/fail with timing. Supports GET, POST, PUT, DELETE with auth headers, JSON bodies, and batch test suites. Useful for quick debugging, post-deploy verification, and API smoke testing.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/http-api-tester/SKILL.md
```

## How to use

```
"Test my API at https://api.example.com/health"
```

The agent:
1. Makes a GET request to the endpoint
2. Checks the status code
3. Reports: status, response time, body

## Example

```
User: "Run a smoke test on my API after deploy"

Agent runs a test suite:
  PASS: Health check — 200 (45ms)
  PASS: Get users — 200 (120ms)
  PASS: Create user — 201 (89ms)
  PASS: Unauthorized — 401 (12ms)

  4/4 passed. API is healthy.
```
