---
name: mcp-server-build
description: "Build a working MCP server that exposes your tools to AI agents — agent + this skill = user gets a functional Model Context Protocol server."
version: 1.0.0
---

# mcp-server-build

Build a Model Context Protocol (MCP) server that exposes your tools, resources, and prompts to AI agents. MCP is an open protocol that lets AI assistants interact with external systems through a standardized interface.

## When to Use

- The user wants to expose their tools or APIs to an AI agent via MCP.
- The user wants to build an MCP server for a custom service.
- The user says "build an MCP server", "make my tool work with MCP", or "I want my agent to call my API".

## MCP Protocol Basics

MCP servers expose three types of capabilities:

| Capability | What it does |
|---|---|
| **Tools** | Functions the agent can call (e.g., `search_database`, `send_email`) |
| **Resources** | Data the agent can read (e.g., `file://config.json`, `db://schema`) |
| **Prompts** | Pre-built prompt templates the agent can use |

Servers communicate via JSON-RPC over one of two transports:

| Transport | Use case |
|---|---|
| **stdio** | Local servers, launched by the agent process |
| **HTTP** | Remote servers, accessible over the network |

## Workflow

### Step 1: Choose your language and SDK

| Language | SDK | Install |
|---|---|---|
| Python | `mcp` | `pip install mcp` |
| TypeScript | `@modelcontextprotocol/sdk` | `npm install @modelcontextprotocol/sdk` |

### Step 2: Define your tools

Each tool has a name, description, and JSON Schema for its parameters:

```python
from mcp import Server, Tool
from mcp.types import ToolSchema

server = Server("my-server")

@server.tool()
async def search_database(query: str, limit: int = 10) -> str:
    """Search the database for matching records.

    Args:
        query: The search query string
        limit: Maximum number of results to return
    """
    # Your search logic here
    results = await db.search(query, limit=limit)
    return json.dumps(results)
```

### Step 3: Implement handlers

The handler is the function that runs when the agent calls the tool. It receives the arguments as a dict and returns a string (or structured content).

```python
@server.tool()
async def get_file(path: str) -> str:
    """Read a file from the local filesystem."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at {path}"
    except PermissionError:
        return f"Error: Permission denied for {path}"
```

### Step 4: Register resources (optional)

Resources are URIs the agent can read:

```python
@server.resource("config://app")
async def get_config() -> str:
    """Return the application configuration."""
    return json.dumps({"version": "1.0", "debug": False})
```

### Step 5: Choose transport and run

**stdio (local):**
```python
import asyncio
from mcp.server.stdio import stdio_server

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

asyncio.run(main())
```

**HTTP (remote):**
```python
from mcp.server.sse import sse_server

async def main():
    async with sse_server("0.0.0.0", 8080) as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

asyncio.run(main())
```

### Step 6: Test with an MCP client

```bash
# Using the MCP inspector (comes with the SDK)
mcp inspect python my_server.py

# Or connect from an agent that supports MCP
# Hermes: hermes mcp add my-server --command "python my_server.py"
# Claude Desktop: add to claude_desktop_config.json
```

## Tool Schema

Every tool needs a clear JSON Schema so the agent knows what arguments to pass:

```python
TOOL_SCHEMA = {
    "name": "search_database",
    "description": "Search the database for matching records.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return",
                "default": 10
            }
        },
        "required": ["query"]
    }
}
```

Good descriptions are critical — the agent uses them to decide when to call the tool.

## Full Example: File Search Server

```python
#!/usr/bin/env python3
import asyncio
import json
import os
from mcp import Server
from mcp.server.stdio import stdio_server

server = Server("file-search")

@server.tool()
async def search_files(directory: str, pattern: str) -> str:
    """Search for files matching a pattern in a directory.

    Args:
        directory: The root directory to search in
        pattern: Filename pattern (e.g., '*.py', '*.json')
    """
    import fnmatch
    matches = []
    for root, dirs, files in os.walk(directory):
        for filename in fnmatch.filter(files, pattern):
            matches.append(os.path.join(root, filename))
    return json.dumps(matches[:50], indent=2)

@server.tool()
async def read_file(path: str) -> str:
    """Read the contents of a file."""
    try:
        with open(path, 'r') as f:
            return f.read()[:10000]  # cap at 10k chars
    except Exception as e:
        return f"Error: {e}"

@server.resource("stats://file-search")
async def get_stats() -> str:
    """Return search statistics."""
    return json.dumps({"server": "file-search", "version": "1.0"})

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
```

## Connecting to Hermes

```bash
# Add as a stdio server
hermes mcp add file-search --command "python /path/to/file_search_server.py"

# Add as an HTTP server
hermes mcp add file-search --url http://localhost:8080

# Test the connection
hermes mcp test file-search

# List available tools from the server
hermes mcp list
```

## Pitfalls

- **Vague tool descriptions** — The agent decides whether to call a tool based on its description. "Searches stuff" won't be called. "Searches the database for records matching a query string, returns up to N results as JSON" will.
- **No error handling** — Tools that crash on bad input will break the agent's workflow. Always return error messages as strings, never raise unhandled exceptions.
- **Returning too much data** — Agents have context limits. Cap returns at a reasonable size (10k chars, 50 results) and let the agent ask for more if needed.
- **No input validation** — Validate paths, queries, and parameters before processing. Don't trust the agent to send valid input.
- **Blocking operations** — MCP handlers should be async. If you have blocking I/O (file reads, database queries), run them in a thread executor.
- **Transport mismatch** — stdio servers are launched by the agent process. HTTP servers need to be running independently. Don't try to serve HTTP over stdio or vice versa.
