---
description: "Quick reference for the MCP tools used by this project and how to discover/use them"
applyTo: '**'
---

# MCP services cheat-sheet

Purpose: provide a compact reference for the MCP-style tools referenced in the codebase and the helper functions we use when integrating with MCP servers (Context7, Memory MCPs, sequential-thinking MCPs). Links point to primary docs and MCP discovery pages so you can install or inspect servers locally.

High-level pointers

- Context7 (and similar servers) expose library/documentation tools (resolve-library-id, get-library-docs). Context7 is a popular example and docs are here:
  - Context7 (project pages / docs): https://github.com/upstash/context7
  - Context7 overview / install examples: https://claudemcp.com/servers/context7

- Memory MCP servers implement a knowledge-graph / memory API (create/read/delete nodes, add observations, relations). Many MCP memory servers exist — search the MCP servers gallery and refer to the server's API to learn exact parameter names.
  - MCP servers list / examples: https://code.visualstudio.com/mcp
  - Community memory MCP (examples & implementations): search for "memory mcp server" (Context/Community pages linked above)

Function reference (the functions listed in the repository and what they map to)

- mcp_context7_resolve-library-id
  - Purpose: given a library name (e.g. "react", "next.js"), return the Context7-compatible library id used internally by Context7 (for example: `/vercel/next.js`).
  - Typical server: Context7 (or any library-docs MCP server).
  - How to use: first call resolve-library-id with `libraryName`, then use the returned id with get-library-docs.
  - Docs / install: https://github.com/upstash/context7 and https://claudemcp.com/servers/context7

- mcp_context7_get-library-docs
  - Purpose: fetch focused documentation or code examples for a library identified by a Context7-compatible ID.
  - Inputs: `context7CompatibleLibraryID` (required), `topic` (optional), `tokens` (optional).
  - Typical server: Context7.
  - Notes: this is the primary tool you call when you need up-to-date, version-specific docs inside an LLM prompt.

- mcp_memory_*
  - Purpose: CRUD and query operations against a Memory MCP server (knowledge graph / vector store / observation storage). The repository includes helpers with the following names:
    - mcp_memory_add_observations — add one or more observations to an entity/node
    - mcp_memory_create_entities — create new nodes/entities
    - mcp_memory_create_relations — create relations between entities
    - mcp_memory_delete_entities — remove entities and their relations
    - mcp_memory_delete_observations — remove observations from an entity
    - mcp_memory_delete_relations — remove relations
    - mcp_memory_open_nodes — fetch one or more nodes by name
    - mcp_memory_read_graph — dump or read an exported graph snapshot
    - mcp_memory_search_nodes — search nodes by text or metadata
  - Typical servers: Memory MCP servers (implementations vary). Consult the specific server's docs for exact payload shapes.
  - Discovery tip: add a Memory MCP to VS Code (or your MCP client) and use the MCP inspector to examine the tool signatures and example inputs.

- mcp_sequentialthi_sequentialthinking
  - Purpose: a sequential-thinking MCP exposes a multi-step planning or chain-of-thought style tool that agents can call to break a task into ordered sub-steps. This can be useful to run deterministic multi-step strategies inside an MCP-enabled agent.
  - Typical server: sequential-thinking MCP implementations are experimental/community projects; Context7 and other MCP ecosystems discuss sequential-thinking tools.
  - Notes: behavior and inputs vary significantly between implementations; inspect the server's tool descriptor to learn the exact calls.

Usage checklist (practical steps)
1. Add the MCP server you want to use to your MCP client (VS Code `.vscode/mcp.json`, Cursor, Claude Desktop, etc.). See VS Code docs: https://code.visualstudio.com/docs/copilot/chat/mcp-servers
2. Start the server and run a discovery/listing command (or use the MCP inspector) to see the exact tool names and parameter shapes.
3. Use `resolve-library-id` (Context7) to normalize library names, then call `get-library-docs` with the returned ID to fetch documentation snippets.
4. For memory operations, call the server's create/read/search tools and follow the returned schemas; tests should use the MCP inspector or the server's example payloads when constructing inputs.
5. For Python/Pylance helpers, add the Pylance MCP server and use the tool discovery results to learn how to call file checks, refactors, and environment queries.

References & links
- VS Code MCP servers: https://code.visualstudio.com/docs/copilot/chat/mcp-servers
- Model Context Protocol (spec): https://modelcontextprotocol.io/
- Context7 (library docs MCP): https://github.com/upstash/context7 and https://claudemcp.com/servers/context7
- Claude MCP community (examples & servers list): https://claudemcp.com/
- MCP servers gallery (VS Code curated list): https://code.visualstudio.com/mcp
