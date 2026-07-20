# github-actions-ci

> Ship a real GitHub Actions CI/CD pipeline for any project — tests, builds, and
> deployments that actually pass, generated from a single conversation.

Part of the [Hermes Skills Portfolio](https://github.com/MonicaAmano/hermes-skills-portfolio)
by **Monica Amano**.

---

## What it does

`github-actions-ci` turns "can you add CI to my repo?" into a working
`.github/workflows/*.yml` file plus the supporting config to make it green. It
covers the full pipeline lifecycle:

- **Test** — run your suite on every push and pull request
- **Build** — compile, bundle, and upload artifacts
- **Deploy** — ship to hosts, registries, or Pages on merge to `main`
- **Matrix** — parallelize across OSes and language versions
- **Secrets** — OIDC and encrypted secret handling done right
- **Caching** — slash build times with dependency caches
- **Pitfalls** — the 10 mistakes that break real pipelines, avoided by default

## Why use it

Writing YAML by hand means re-learning the same footguns every time: forgetting
`checkout`, pinning to a mutable `@main`, leaking a secret to logs, or watching
`npm install` produce a non-reproducible build. This skill bakes in the
battle-tested defaults so the pipeline works the first time and stays safe.

## Install

Install the skill into your Hermes agent:

```bash
hermes skills install \
  https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/github-actions-ci/SKILL.md
```

Or add it to your portfolio checkout and point Hermes at the directory.

## Usage

Just ask your agent naturally:

- "Add CI that runs my pytest suite on Python 3.11 and 3.12"
- "Set up GitHub Actions to build my Next.js app and deploy to Pages"
- "Make my workflow test on Ubuntu, macOS, and Windows with Node 18/20/22"
- "Why is my deploy firing on every PR? Fix it."

The skill inspects your stack, emits the correct workflow, and walks a
deliverable checklist (checkout first, pin actions, gate deploys, protect
secrets) before calling it done.

## Example output

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
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm test -- --ci
```

## License

MIT — free to use, fork, and extend.
