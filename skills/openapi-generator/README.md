# openapi-generator

> Generate client SDKs, server stubs, API docs, and config from an OpenAPI spec — in 50+ languages, straight from the contract.

Part of the [Hermes Skills Portfolio](https://github.com/THEROCKSSS/hermes-skills-portfolio) by **Monica Amano**.

---

## What it does

Point the skill at an OpenAPI 2.0 / 3.0 / 3.1 specification and it produces
real, buildable code — no hand-written boilerplate:

- **Client SDKs** — typed clients for TypeScript, Python, Go, Java, C#, Rust, Swift, and more.
- **Server stubs** — routing, models, and interfaces to implement on Spring, FastAPI, Express, ASP.NET Core, and others.
- **Documentation** — HTML, Markdown, AsciiDoc, and Redoc sites generated from the same contract.
- **Infrastructure** — Kubernetes, Terraform, and Postman collections from the spec.

---

## Why you want it

| Without this skill | With this skill |
|--------------------|-----------------|
| Hand-write a client per language | One spec → every client in minutes |
| Drift between docs and code | Docs generated from the same source of truth |
| Guess generator flags | Correct, version-pinned invocations |
| Hit Docker/JAR pitfalls blind | Guided around the common traps |

---

## Quick start

```bash
# Generate a TypeScript fetch client from your spec
docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli generate \
  -i /local/openapi.yaml \
  -g typescript-fetch \
  -o /local/out/typescript
```

Prefer npm or the JAR? The skill documents all three install paths
(Docker, JAR, npm wrapper) plus version pinning for reproducible output.

---

## Highlights

- ✅ 50+ generator targets with verified canonical names
- ✅ Client, server, and documentation generator recipes
- ✅ `additional-properties` and `config.json` customization patterns
- ✅ Spec validation with built-in and Spectral linting
- ✅ A dedicated **Pitfalls** section: Docker mounts, `$ref` resolution, version drift, overwriting hand-written code, JVM memory, 3.1 support

---

## Install

Add this skill to your Hermes agent:

```
https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/openapi-generator/SKILL.md
```

Then ask your agent things like:

- *"Generate a Python client and a Spring server stub from my openapi.yaml."*
- *"Build HTML docs from this spec and pin the generator version."*
- *"Create a TypeScript SDK with ES6 support and a custom package name."*

---

## License

MIT — contributions welcome via the portfolio repository.
