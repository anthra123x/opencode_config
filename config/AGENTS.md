<!-- codebase-memory-mcp:start -->
# Codebase Knowledge Graph (codebase-memory-mcp)

NOTE: These tools require codebase-memory-mcp to be installed and running.
If you get "tool not found" errors, fall back to grep/glob immediately.

This configuration uses codebase-memory-mcp to maintain a knowledge graph of the codebase.
Always prefer MCP graph tools over grep/glob for structural code discovery.

## Priority Order
1. `search_graph` — find functions, classes, routes, variables by pattern
2. `trace_path` — trace callers/callees of a function
3. `get_code_snippet` — read specific function/class source code
4. `query_graph` — run Cypher queries for complex multi-hop patterns
5. `get_architecture` — high-level project overview

## When to fall back to grep/glob
- Searching for string literals, error messages, config values
- Searching non-code files (Dockerfiles, shell scripts, configs)
- When MCP tools return insufficient results

## Examples
- Find a handler: `search_graph(name_pattern=".*AuthHandler.*")`
- Who calls it: `trace_path(function_name="AuthHandler", direction="inbound")`
- Read source: `get_code_snippet(qualified_name="src/auth.AuthHandler")`
<!-- codebase-memory-mcp:end -->
