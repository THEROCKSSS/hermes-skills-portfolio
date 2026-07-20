---
name: github-actions-ci
description: >-
  Design, author, and debug GitHub Actions CI/CD workflows for any project.
  Use when a user wants automated testing, builds, deployments, matrix
  builds, caching, or secret handling on GitHub. Produces a working
  .github/workflows YAML file tailored to their language and stack.
version: 1.0.0
---

# GitHub Actions CI/CD

Turn a user's project into a repo with a real, working continuous integration
and continuous deployment pipeline. This skill produces a correct
`.github/workflows/*.yml` file plus the supporting configuration needed to make
it pass.

## When to Use

Invoke this skill when the user:

- Asks for "CI", "continuous integration", "GitHub Actions", "pipeline", or
  "automated tests on push".
- Wants every push/PR to run tests or a build before merge.
- Wants to deploy automatically to a host, container registry, cloud, or
  Pages on merge to `main`.
- Has flaky, slow, or broken workflows that need fixing.
- Needs matrix builds across OSes, language versions, or dependency versions.
- Is setting up a new repo and wants a sane baseline pipeline.

Do **not** use it for other CI providers (GitLab CI, CircleCI, Jenkins,
Travis). Those have different syntax and deserve their own skills.

## Workflow Syntax

A workflow is a YAML file in `.github/workflows/`. The minimal skeleton:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: echo "add your test command here"
```

Key top-level keys:

- `name` — human-readable pipeline name shown in the GitHub UI.
- `on` — trigger. Can be a string, list, or map with `push`/`pull_request`/
  `workflow_dispatch`/scheduled `schedule` (cron) etc.
- `jobs` — a map of jobs. Each job has `runs-on`, `steps`, and optional
  `needs`, `strategy`, `env`, `services`, `permissions`, `concurrency`.
- `steps` — a list. Each step is either `uses:` (an action) or `run:`
  (a shell command), plus `name:`, `env:`, `if:`, `with:`, `id:`.

Critical rules:

1. Always pin actions to a major version tag (`actions/checkout@v4`), never a
   branch like `@main` in production — branch refs are mutable and a supply-chain
   risk. Use SHAs for maximum security.
2. `actions/checkout@v4` is required before any step that reads repo files.
3. Use `shell:` to force an interpreter (`bash`, `pwsh`, `python`). Default on
   Linux/macOS is `bash`, on Windows is `pwsh`.
4. Indentation is YAML — two spaces, no tabs. A single stray tab breaks parse.

## Common Patterns

### Test

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm test -- --ci
```

Rule of thumb: `npm ci` (clean install from lockfile) over `npm install` in CI.
For Python use `actions/setup-python@v5` + `pip install -r requirements.txt`
and `pytest`. Fail the job by returning a non-zero exit code — Actions does
that for you automatically.

### Build

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

Upload build outputs with `actions/upload-artifact@v4` so later jobs (or
humans) can download them. Note: artifact actions v3 and v4 are NOT
interoperable — keep both upload and download on the same major version.

### Deploy

```yaml
jobs:
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist
      - name: Deploy to production
        run: ./scripts/deploy.sh
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
```

Gate deploys with `if: github.ref == 'refs/heads/main'` so PRs never deploy,
and `needs:` to ensure the build/test job passed first.

## Matrix Builds

Run the same job across many configurations in parallel via `strategy.matrix`:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        node: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
          cache: npm
      - run: npm ci
      - run: npm test
```

- `fail-fast: false` lets all matrix legs finish even if one fails — better for
  seeing the full picture.
- `max-parallel` caps concurrency if you hit runner limits.
- Add `include:` to append extra dimensions and `exclude:` to drop
  combinations you don't care about.

## Secrets Management

Never hardcode credentials. Store them in **Settings → Secrets and variables →
Actions** as repository (or environment) secrets, then reference them as
`${{ secrets.NAME }}`.

```yaml
steps:
  - name: Publish package
    run: npm publish
    env:
      NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Rules:

- Secrets are redacted in logs; never `echo` them. If you must debug, log only
  `${{ secrets.TOKEN != '' }}` (prints `true`/`false`) to confirm presence.
- Prefer **OpenID Connect (OIDC)** over static keys for cloud deploys
  (AWS, GCP, Azure). Use `actions/configure-aws-credentials@v4` with
  `role-to-assume` so no long-lived key is stored.
- Scope secrets to an `environment:` (e.g. `production`) to require manual
  approval and restrict who can consume them.
- `GITHUB_TOKEN` is auto-provided; for cross-repo pushes, mint a Personal
  Access Token and store it as a secret.

## Caching

Cache dependencies to slash build times:

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: 20
    cache: npm          # auto-caches ~/.npm

# For anything else:
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

- The `cache:` shortcut on `setup-*` actions is the cleanest path for Node,
  Python, Ruby, Go.
- For arbitrary folders use `actions/cache@v4` with a `key` that includes a hash
  of the lockfile so the cache busts when dependencies change.
- `restore-keys` provides a prefix match fallback when the exact key misses.
- Cache size limit is ~10 GB and caches are scoped per-branch/PR by default.

## Pitfalls

1. **Missing checkout.** Steps read an empty workspace without
   `actions/checkout@v4` first. Always check it out.
2. **Mutable action refs.** `@main` or `@master` can change under you and is a
   supply-chain risk. Pin to `@v4` or a commit SHA.
3. **`npm install` instead of `npm ci`.** `install` ignores the lockfile and can
   produce non-reproducible builds; `ci` fails if lockfile is out of sync.
4. **Artifact version mismatch.** Mixing `upload-artifact@v3` with
   `download-artifact@v4` fails. Keep them aligned.
5. **Secrets in logs.** Printing a secret (even in a failed step) leaks it into
   build logs. Reference via `env:`, never `run: echo "$SECRET"`.
6. **Wrong trigger.** `on: push` with no `branches:` runs on every branch;
   `pull_request` never fires on direct pushes. Be explicit.
7. **`continue-on-error` abuse.** It marks a job green even when it fails —
   useful only for experimental matrix legs, never for your real test gate.
8. **Windows line endings.** `git autocrlf` can break shell scripts on
   `windows-latest`. Set `shell: bash` or normalize line endings.
9. **No `concurrency` group.** Concurrent pushes can race deploys. Use:
   ```yaml
   concurrency:
     group: deploy-${{ github.ref }}
     cancel-in-progress: true
   ```
10. **Timeouts.** Long jobs may exceed the default. Add `timeout-minutes:` to
    jobs to fail fast and free runners.

## Deliverable Checklist

When finishing, confirm:

- [ ] Workflow file lives at `.github/workflows/<name>.yml`.
- [ ] `actions/checkout@v4` is the first step of every job that needs code.
- [ ] Actions are pinned to major versions.
- [ ] Test command matches the project's actual test runner.
- [ ] Secrets are referenced via `${{ secrets.* }}`, never inline.
- [ ] Deploy jobs are gated by `if: github.ref == 'refs/heads/main'`.
- [ ] A `concurrency` group protects any deploy/publish job.
