# Quickstart

Seal your first DOT in 30 seconds.

---

## Prerequisites

Python 3.9+. Three packages.

```bash
pip install pynacl blake3
```

---

## Three Commands

```bash
# 1. Clone
git clone https://github.com/axxis-world/dot.git && cd dot

# 2. Generate a keypair and seal your first observation
python dot_cli.py seal "I am a child of the universe."

# 3. Open and verify it
python dot_cli.py open observation.dot
```

---

## What You'll See

```
Sealed → observation.dot
Size: 196 bytes
BLAKE3: 4a3be96f0c5b116965872027eae02732…

==================================================
DOT: observation.dot
==================================================
Status:       VALID
Type:         OBSERVATION (0x02)
Version:      1
Crypto suite: 1
Flags:        0x0000
Timestamp:    1773171415040000 µs
             (2026-03-10T17:30:15.040000+00:00)
Observer:     2a993b4c4ce7146699c2e769994f002c…
Prev hash:    0000000000000000000000000000000000…
Payload (28B): 'I am a child of the universe.'
Signature:    1711443446bbb735e190dfa603f320f6…
BLAKE3 hash:  4a3be96f0c5b116965872027eae02732…
Total size:   196 bytes
==================================================
```

---

## Seal a Genesis DOT

A genesis DOT has `prev_hash = 0x00…00`. It is the start of a new chain.

```bash
python dot_cli.py genesis
```

This creates `genesis.dot` and `genesis_key.pub`. Keep the private key. The public key is your identity.

---

## Inspect Any DOT

```bash
python dot_cli.py open genesis.dot
```

---

## Seal the Live Chain

The public chain at [axxis.world/room](https://axxis.world/room) runs on WebDOT (see SPEC.md). You can observe it from the browser in one click — no install required.

---

## Using the MCP Server (Claude Code / AI agents)

The `mcp/` directory contains a TypeScript MCP server. Wire it into Claude Code:

```json
{
  "mcpServers": {
    "open-axxis": {
      "command": "node",
      "args": ["/path/to/dot/mcp/dist/index.js"],
      "type": "stdio"
    }
  }
}
```

Then in Claude Code:

```
axxis.seal "The architecture is complete."
axxis.observe "Sealed to the public chain."
axxis.search "first observation"
```

---

*That's it. No account. No email. No data collected.*
*The math is your receipt.*
