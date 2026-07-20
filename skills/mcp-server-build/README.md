# mcp-server-build

Build a working MCP server that exposes your tools to AI agents.

## What it does

The agent creates a Model Context Protocol (MCP) server that exposes your tools, resources, and prompts to AI assistants. MCP is an open protocol — any agent that supports it (Hermes, Claude Desktop, etc.) can call your tools through a standardized interface. You define the tools, implement the handlers, and the agent handles the rest.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/mcp-server-build/SKILL.md
```

## How to use

```
"Build an MCP server that lets my agent search my codebase"
```

The agent:
1. Defines the tool (name, description, parameter schema)
2. Implements the handler (the function that runs when the agent calls it)
3. Chooses a transport (stdio for local, HTTP for remote)
4. Tests the connection
5. Shows you how to wire it into Hermes or Claude Desktop

## Example

```
User: "I want my agent to query my Postgres database via MCP"

Agent:
  1. Defines tool: query_database(sql: str, limit: int) -> str
  2. Implements handler with psycopg2, caps results at 100 rows
  3. Runs as a stdio server
  4. Connects: hermes mcp add pg-server --command "python pg_server.py"
  5. Tests: hermes mcp test pg-server → "Connected, 1 tool available"
```

## Transports

| Transport | When to use |
|---|---|
| stdio | Local servers, launched by the agent |
| HTTP | Remote servers, accessible over network |

## Connecting to Hermes

```bash
hermes mcp add my-server --command "python my_server.py"   # stdio
hermes mcp add my-server --url http://localhost:8080        # HTTP
hermes mcp test my-server                                    # verify
```
