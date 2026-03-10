# DOT MCP Server (TypeScript)

A [Model Context Protocol](https://modelcontextprotocol.io) server that exposes the DOT protocol as AI tools.

## Tools

| Tool | Description |
|------|-------------|
| `axxis.seal` | Seal a new DOT observation (Ed25519, SHA-256 chain) |
| `axxis.verify` | Verify a DOT's signature and chain integrity |
| `axxis.observe` | Seal + submit to the public chain at axxis.world |
| `axxis.room` | Read the live DOT chain |
| `axxis.search` | Semantic search across all DOTs (all-MiniLM-L6-v2) |

## Install

```bash
npm install
npm run build
```

## Use with Claude Code

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "open-axxis": {
      "command": "node",
      "args": ["/path/to/mcp/dist/index.js"],
      "type": "stdio"
    }
  }
}
```

## Tech

- Ed25519 via `@noble/ed25519`
- SHA-256 chain hashing
- Local embedding cache: `~/.axxis/embed-cache.json`
- Model: `Xenova/all-MiniLM-L6-v2` (25MB, Apache 2.0)
