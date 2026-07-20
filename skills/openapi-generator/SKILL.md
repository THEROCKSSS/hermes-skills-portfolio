---
name: openapi-generator
description: >-
  Generate client SDKs, server stubs, API documentation, and infrastructure
  from an OpenAPI 2.0/3.x specification using openapi-generator-cli. Supports
  50+ languages and frameworks. Use when a user has an OpenAPI/Swagger spec and
  wants typed clients, server skeletons, docs, or config without hand-writing
  boilerplate.
version: 1.0.0
---

# openapi-generator

Turn an OpenAPI specification into working code. This skill wraps
[OpenAPI Generator](https://openapi-generator.tech) so an agent can produce
client SDKs, server stubs, documentation, and supporting config directly from a
spec file — with the right flags, the right generator, and none of the common
pitfalls.

## When to Use

Load this skill when the user:

- Has an OpenAPI 2.0 (Swagger) or 3.0/3.1 spec and wants a **client SDK** in a
  specific language (TypeScript, Python, Go, Java, C#, Ruby, etc.).
- Wants a **server stub** / skeleton to implement an API described by a spec.
- Needs **API documentation** (HTML, Markdown, AsciiDoc, Redoc) generated from a
  spec.
- Asks to scaffold a new project "from the API contract".
- Wants to keep generated clients/stubs in sync with a changing spec.
- Mentions Swagger Codegen, `openapi-generator`, `openapi-generator-cli`,
  `nswag`, or "generate a client from this YAML/JSON".

Do **not** use this for: writing the OpenAPI spec itself (that's design work),
runtime API mocking (use Prism/httpbin), or contract testing (use Dredd/Schemathesis).
This skill is about *code generation from an existing spec*.

## openapi-generator-cli

The CLI is distributed as a Java JAR, Docker image, and native installers. Pick
one and reuse it for every generation in a session.

### Option A — Docker (recommended, no Java install)

```bash
# List every available generator
docker run --rm openapitools/openapi-generator-cli list

# Generate a TypeScript fetch client
docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli generate \
  -i /local/openapi.yaml \
  -g typescript-fetch \
  -o /local/out/typescript
```

The `-v "${PWD}:/local"` bind mount is mandatory — the container writes output
into `/local`, which maps to your working directory.

### Option B — JAR (needs Java 11+)

```bash
curl -L https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.6.0/openapi-generator-cli-7.6.0.jar \
  -o openapi-generator-cli.jar

java -jar openapi-generator-cli.jar list
java -jar openapi-generator-cli.jar generate -i openapi.yaml -g python -o out/python
```

### Option C — npm wrapper (single-binary, no Java)

```bash
npm install -g @openapitools/openapi-generator-cli
openapi-generator-cli version-manager set 7.6.0
openapi-generator-cli generate -i openapi.yaml -g go -o out/go
```

Pin a specific version (`openapi-generator-cli version-manager set 7.6.0`) so
generated output is reproducible across machines.

## Generator Types

### Client

Generates a typed SDK to *call* the API. Most common request.

```bash
openapi-generator-cli generate \
  -i openapi.yaml -g typescript-fetch -o sdk/ts \
  --additional-properties=supportsES6=true,npmName=my-api-sdk,npmVersion=1.0.0
```

Common client generators: `typescript-fetch`, `typescript-axios`, `python`,
`java`, `go`, `csharp-netcore`, `ruby`, `php`, `rust`, `kotlin`, `swift5`, `dart`.

### Server

Generates a server stub with routing, models, and (optionally) business-logic
stubs you fill in.

```bash
openapi-generator-cli generate \
  -i openapi.yaml -g spring -o server/java \
  --additional-properties=interfaceOnly=true,useSpringBoot3=true
```

Common server generators: `spring` (Java), `flask` / `fastapi` (Python),
`express` (Node), `go-server`, `aspnetcore` (C#), `ruby-on-sinatra`, `php-symfony`.

Use `interfaceOnly=true` to emit just the interfaces/models — ideal when you
already have a framework set up and only want the contract types.

### Documentation

```bash
# Static HTML2 docs
openapi-generator-cli generate -i openapi.yaml -g html2 -o docs/html

# Markdown
openapi-generator-cli generate -i openapi.yaml -g markdown -o docs/md

# AsciiDoc
openapi-generator-cli generate -i openapi.yaml -g asciidoc -o docs/ascii
```

Other doc-ish generators: `openapi` (normalizes/re-exports the spec),
`openapi-yaml`, `redoc` (bundles Redoc viewer), `confluencewiki`.

## Language Support

OpenAPI Generator supports **50+ targets**. The agent should verify the exact
generator name before invoking — names are case-sensitive and change between
versions. Run `list` (Docker/JAR) or `openapi-generator-cli list` (npm) and grep
for the language.

```bash
docker run --rm openapitools/openapi-generator-cli list | grep -i typescript
```

High-traffic families and their canonical generator names:

| Family     | Generator(s)                                  |
|------------|------------------------------------------------|
| TypeScript | `typescript-fetch`, `typescript-axios`, `typescript-node` |
| Python     | `python`, `python-fastapi`                     |
| Go         | `go`, `go-server`                              |
| Java       | `java`, `spring`                               |
| C#         | `csharp-netcore`, `aspnetcore`                 |
| Rust       | `rust`, `rust-server`                          |
| Kotlin     | `kotlin`, `kotlin-spring`                      |
| Swift      | `swift5`                                       |
| PHP        | `php`, `php-symfony`, `php-laravel`            |
| Ruby       | `ruby`, `ruby-on-sinatra`                      |

If a user asks for a language not listed by `list`, tell them it is unsupported
rather than guessing a generator name — a wrong name fails loudly.

## Customization

Generators are configured with `--additional-properties` (comma-separated
`key=value`) and `-c config.json` for many properties.

```bash
openapi-generator-cli generate -i openapi.yaml -g python -o out/python \
  -c config.json
```

`config.json`:

```json
{
  "packageName": "my_api_client",
  "projectName": "my-api-client",
  "packageVersion": "2.1.0",
  "generateSourceCodeOnly": false,
  "useOneOfDiscriminatorLookup": true
}
```

Useful properties (generator-specific — always confirm with `config-help`):

```bash
openapi-generator-cli config-help -g typescript-fetch
```

- `useOneOfDiscriminatorLookup`, `useInlineModelResolver` — shape of models.
- `enumClassPrefix`, `enumNameMappings` — enum naming.
- `hideGenerationTimestamp` — set `true` to keep diffs clean in version control.
- `sourceFolder`, `apiPackage`, `modelPackage` — output layout.

For deeper changes (custom templates, license headers, naming), use the
`-t templates/` flag to supply a Mustache template directory. Copy the default
templates first:

```bash
openapi-generator-cli author template -g typescript-fetch -o my-templates/
```

## Validation

Validate the spec before generating — most failures trace back to an invalid or
partially-resolved spec.

```bash
# Built-in structural validation
openapi-generator-cli validate -i openapi.yaml

# Stronger linting with Spectral (separate tool)
npm install -g @stoplight/spectral-cli
spectral lint openapi.yaml
```

Workflow the agent should follow:

1. `validate` the spec — fix schema/reference errors first.
2. `list` / `config-help` to confirm generator name and properties.
3. `generate` into a clean output directory.
4. Inspect the output: does `out/<lang>/README.md` / build file exist?
5. For client/server, optionally compile/build the generated project to confirm
   it is non-trivial and importable.

```bash
# Example check after generating a Python client
cd out/python && python -m pip install -e . && python -c "import openapi_client"
```

## Pitfalls

- **Mounting the spec into Docker.** Forgetting `-v "${PWD}:/local"` means the
  container cannot see your spec and writes nothing where you expect. Always bind
  the working directory.
- **`$ref` must resolve.** Remote `$ref`s (URLs) work online but break in
  air-gapped runs. Bundle first with `openapi-generator-cli merge` or
  `swagger-cli bundle` to inline all references.
- **Version drift.** Different CLI versions emit different code. Pin the version
  and record it in the generated project's README or a `Makefile`/CI step.
- **Overwriting hand-written code.** Never generate into a directory that
  contains source you edited. Use `interfaceOnly=true` or generate into a
  dedicated `generated/` subtree and import it.
- **`hideGenerationTimestamp`.** Leave it off during debugging, but set it
  `true` for committed code so regeneration doesn't create noisy diffs.
- **Case-sensitive generator names.** `TypeScript-Fetch` fails; the correct
  name is `typescript-fetch`. Always copy the exact string from `list`.
- **Java/JAR memory.** Large specs can OOM the JVM. Raise the heap:
  `java -Xmx2g -jar openapi-generator-cli.jar generate ...`.
- **OpenAPI 3.1 vs 2.0.** Some generators lag on 3.1 features (webhooks,
  discriminators). If a 3.1 spec fails, try converting to 3.0 with
  `openapi-generator-cli merge` or `swagger2openapi`.
- **Don't hand-merge generated folders.** Treat generated code as build
  artifacts; regenerate rather than resolve Git merge conflicts inside them.
- **Docker writes files as root.** Add `--user $(id -u):$(id -g)` to the
  `docker run` command so output files aren't owned by root.
