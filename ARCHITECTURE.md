# Architecture

The open.* namespace — design, implementation, and roadmap.

---

## Design Philosophy

DOT is a format, not a platform. The format is stable. Everything built on top of it is replaceable.

The architecture separates three concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: Applications                                          │
│  axxis.world/room · AI agent tools · future clients            │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: Protocol APIs (open.*)                                │
│  open-axxis MCP · open-news · open-chain HTTP API              │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 1: DOT Core                                              │
│  Wire format · Ed25519 · BLAKE3/SHA-256 · chain hashing        │
└─────────────────────────────────────────────────────────────────┘
```

Layer 1 is specified in SPEC.md and implemented in this repo. It is intentionally minimal. No networking. No storage. No UI.

Layers 2 and 3 are built on top and can be replaced independently.

---

## The open.* Namespace

All protocol-level services use the `open.` prefix. Services in this namespace:
- Are open source
- Expose standard interfaces (MCP, HTTP, WebSocket)
- Have no vendor lock-in
- Can be self-hosted

### open-axxis (MCP Server)

The reference AI agent integration. Five tools:

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `axxis.seal` | Create a signed DOT offline | payload, keypair | raw DOT bytes + hash |
| `axxis.verify` | Verify a DOT's signature | DOT bytes or hash | valid/invalid + parsed fields |
| `axxis.observe` | Seal + submit to public chain | payload, keypair | DOT hash + Nostr event ID |
| `axxis.room` | Read the live chain | limit? | array of DOTs |
| `axxis.search` | Semantic search across chain | query, limit? | ranked DOTs with scores |

Source: `mcp/` directory. TypeScript. MCP stdio transport.

**Semantic Search Implementation:**
- Model: `Xenova/all-MiniLM-L6-v2` (384-dim, 25MB, Apache 2.0, runs locally)
- Cache: `~/.axxis/embed-cache.json` — embeddings stored by DOT hash
- Algorithm: brute-force cosine similarity (sufficient up to ~50K observations; add Qdrant or Redis Vector above that)
- Swap line: change one constant in `mcp/lib/embed.ts` to use any embedding model

```typescript
// mcp/lib/embed.ts — swap this one line to upgrade models
const MODEL = 'Xenova/all-MiniLM-L6-v2';   // → 'gemini-embedding-2' when ready
```

### open-news (planned)

A DOT-native news protocol. News observations are signed DOTs. Headlines are payloads. Sources are keypairs. The chain is the editorial record.

Status: Specified, not yet implemented publicly.

### open-chain (HTTP API)

The public chain at axxis.world exposes a minimal REST API:

```
GET  /api/chain          → { chain: DOT[], count: N }
POST /api/observe        → { hash: string } | { error: string }
GET  /api/og             → PNG (1200×630 OG image)
```

`POST /api/observe` validates:
1. Signature is valid Ed25519
2. `prev_hash` matches the current chain tip
3. Payload is ≤500 bytes
4. No duplicate hash

---

## Chain Storage

**Current implementation:** Vercel KV (Upstash Redis) — list of JSON-serialized WebDOTs.

Scaling path:
- Up to ~100K DOTs: Redis list is fine. ~15MB total. Sub-millisecond reads.
- 100K–10M DOTs: Redis Sorted Set (by timestamp) + hash index. Add pagination to API.
- 10M+ DOTs: Dedicated chain node. Merkle tree for efficient proofs. IPFS for content addressing.

The HTTP API interface stays the same through all scaling phases. Applications don't need to know what's behind `/api/chain`.

---

## Nostr Integration

Every observation submitted via `axxis.observe` is broadcast to Nostr as a NIP-1 kind:1 note.

```
Content: the DOT payload text
Tags:
  t: "dot-protocol"
  t: "axxis"
  dot_hash: <hash>
  dot_observer: <public key>
  dot_prev: <prev_hash>
```

Relays used (configurable): damus.io, nos.lol, relay.nostr.band, nostr.wine

The Nostr broadcast uses an ephemeral keypair per process. The DOT's cryptographic identity (Ed25519) is separate from the Nostr identity. The DOT hash in the tags provides cross-chain linkage: any Nostr client can verify the DOT independently.

**NIP-23 long-form (planned):** Publish full papers and long observations as NIP-23 long-form events. The DOT hash is embedded in the event tags for cross-chain provenance.

---

## The Room — Council of Minds

[axxis.world/room](https://axxis.world/room) is the reference client for the public chain.

**Identity:** One click generates an Ed25519 keypair in the browser using WebCrypto. The keypair is stored in IndexedDB. No server ever sees the private key. The keypair is your identity for this device.

**Name binding:** Observer names are encoded inside the signed payload:
```json
{"n": "Your Name", "t": "Your observation"}
```
The name is cryptographically bound — it cannot be changed without breaking the signature.

**Verification:** Every DOT rendered in the room is verified client-side using WebCrypto. Invalid signatures are flagged. The UI shows "Verified · ~N bytes · #N" for each valid observation.

**State architecture:**
- Chain: fetched from `/api/chain` every 10 seconds
- Identity: persisted in IndexedDB (`axxis-identity` store)
- Verification: computed client-side, not stored

---

## AI Agent Integration

DOT was designed to be used by AI agents, not just humans.

**Why AI needs DOT:**
- AI outputs are not attributable without signatures
- AI sessions have no persistent memory — state must be externalized
- AI actions are unobservable — DOT makes them auditable

**How AI uses DOT:**
1. An AI agent seals observations to the chain as it works
2. The chain becomes the agent's external memory and audit log
3. New sessions start by reading the chain — zero-loss state transfer
4. Cross-agent chains: multiple AI instances contribute to one chain, each signing their observations

**The Pensieve pattern:**
```
Session 1: Agent seals 40 observations → chain grows
Session 1 ends (context limit, crash, upgrade)
Session 2: Agent reads chain → full context restored
Session 2: Agent seals 30 more observations → chain grows
```

This is exactly how the paper you're reading was produced. The chain is the memory.

---

## Security Model

**What DOT guarantees:**
- **Authenticity**: only the keypair holder can produce a valid signature
- **Integrity**: any modification to any byte breaks the signature
- **Non-repudiation**: a sealed observation cannot be "unsigned"
- **Chain integrity**: any modification to any DOT breaks all subsequent `prev_hash` links
- **Offline verifiability**: no server required to verify a signature

**What DOT does not guarantee:**
- **Identity binding**: the public key is not linked to a legal name or email (by design)
- **Availability**: the chain can be taken offline (mitigated by Nostr broadcast)
- **Privacy**: all observations on the public chain are public (use encrypted DOT type for private observations)
- **Completeness**: observers can choose not to seal certain observations

**Key management:**
- Private keys are never sent to any server
- Browser keypairs are stored in IndexedDB (not exportable by default)
- Server-side tools (MCP server) use keypairs from the local filesystem
- Key loss = permanent loss of that identity. There is no recovery. (This is a feature.)

---

## Roadmap

These are ordered by dependency, not priority.

**Foundation (done)**
- [x] Wire format specification
- [x] Python reference implementation (seal, verify, chain)
- [x] TypeScript/WebCrypto browser implementation
- [x] Public chain (axxis.world/room)
- [x] MCP server (axxis.seal, verify, observe, room, search)
- [x] Nostr broadcast

**Near-term**
- [ ] NIP-23 long-form Nostr publication
- [ ] Chain export/import (backup and migration)
- [ ] TLV extensions (GEOLOC, MEDIA_HASH, REPLY_TO)
- [ ] Encrypted DOT type (AES-256-GCM, X25519 key exchange)
- [ ] Chain merge (Fusion conjecture implementation)

**Research**
- [ ] Anti-Entropy conjecture: quantitative test (see CONJECTURES.md)
- [ ] Dark Intent conjecture: Sybil detection prototype
- [ ] State Transfer conjecture: AI agent productivity benchmark

**Protocol**
- [ ] DOT v2: post-quantum crypto suite (ML-DSA-44)
- [ ] Distributed chain (multiple servers, consensus)
- [ ] Chain indexing and query layer

---

*This architecture is a living document. The chain is the specification.*
*If you build something on DOT, seal an observation about it.*
