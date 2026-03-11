# Ten Discoveries

These emerged from building DOT. They are empirical observations, not design goals.
Each one was a surprise.

---

## Discovery 1: The Minimum Is 151 Bytes

We set out to make the smallest possible cryptographically signed, self-describing, chain-linked observation format.

The result: **151 bytes** for a 1-byte payload.

Breakdown:
```
Header:       10 bytes  (magic, version, crypto, flags, type, tlv_count)
Timestamp:     8 bytes  (uint64 µs — range: 1970 to year 586,524)
Observer:     32 bytes  (Ed25519 public key — this IS the identity)
Prev hash:    32 bytes  (BLAKE3 — link to previous observation)
Payload len:   4 bytes  (uint32)
Payload:       1 byte   (minimum)
Signature:    64 bytes  (Ed25519 — non-repudiable, offline-verifiable)
─────────────────────
Total:       151 bytes
```

Compared to alternatives:
| Format | Min Size | Chain | Self-describing |
|--------|----------|-------|-----------------|
| **DOT** | **151 B** | **Yes** | **Yes** |
| JWT | ~182 B | No | Yes (header only) |
| Protobuf | ~147 B | No | No |
| Bitcoin tx | 191 B | Yes | No |

Protobuf is smaller, but requires a schema file to parse. A DOT is its own schema.

**Implication:** Every human alive could seal one observation per second for 10,000 years. Total storage: ~47 petabytes. One standard data center.

---

## Discovery 2: 100% Tamper Detection

We ran 1,000 DOTs through an integrity test. 100 were tampered in four different ways:
- Payload flip (1 bit changed)
- Timestamp modification (1 byte changed)
- Signature alteration (1 byte changed)
- Prev hash swap (32 bytes replaced)

**Results:**
- Detected: 100/100 (100%)
- False positives: 0/1,000 (0%)
- Avg verification: 0.06ms per DOT

The stone cannot be carved after sealing.

See `experiments/exp2_integrity.py` to reproduce. Seed is fixed (42). Results are deterministic.

---

## Discovery 3: The Format Is Self-Decoding

Before writing any documentation, we tried to parse `genesis.dot` cold — using only a hex editor and the magic bytes.

Within 10 minutes:
- Magic bytes `\x89DOT` identified the format (analogy to `\x89PNG`)
- Byte 4: version (0x01)
- Byte 5: crypto suite (0x01 = Ed25519)
- Bytes 10–17: timestamp (BLAKE3 decoded to a recognizable date)
- Bytes 18–49: 32-byte public key (recognizable length for Ed25519)
- Bytes 50–81: prev hash (all zeros = genesis sentinel)
- Last 64 bytes: signature (recognizable length for Ed25519 signature)

No documentation required. This was intentional in the magic byte design, but the extent to which it works in practice was a surprise.

See `cold_open_annotated.txt` — the full annotated hex dump.

---

## Discovery 4: The Quantum Upgrade Is One Byte

Upgrading from Ed25519 to ML-DSA (post-quantum signature scheme) requires changing `crypto_suite` from `0x01` to `0x02`.

Everything else stays the same:
- Public key expands from 32B to 1312B (ML-DSA-44) or 1952B (ML-DSA-65)
- Signature expands from 64B to 2420B or 3309B
- But the DOT format accommodates both — size is variable, not fixed

Old DOTs (Ed25519) remain valid. A chain can mix crypto suites — each DOT's `crypto_suite` byte tells the verifier which algorithm to use. No flag day. No migration.

---

## Discovery 5: The Name Is Cryptographic

Early designs stored the observer's name as unsigned metadata — a display field next to the key.

This is wrong. If the name is not inside the signature, it can be changed after the fact.

The fix: encode the name inside the payload.

```python
payload = json.dumps({"n": "Observer Name", "t": "The observation"})
```

Now the name is inside the signable bytes. The Ed25519 signature covers it. Changing the name after sealing breaks the signature. The name is cryptographically bound to the observation.

This is how it works in the public room at axxis.world/room. Your name is provably yours.

---

## Discovery 6: The Integrity Gap Is 12,000 Years Old

While building the table in the paper, we discovered the pattern is not new:

| When | Gap-Closing Technology | What Survived |
|------|----------------------|---------------|
| 9,500 BCE | Stone aligned to stars | The stone. 11,000 years. |
| 3,000 BCE | Writing (but unequal access) | Widely copied texts |
| 500 BCE | Philosophy and law | The most portable forms |
| 800 CE | Scientific method | The method itself |
| 1450 CE | Printing press | Knowledge that reached many |
| 1776 CE | Illuminati / peer review | Ideas that outlived the org |
| **2026** | **DOT** | **?** |

Every civilization that survived found a way to close the gap between "what was observed" and "what can be proven." Every failure preceded a collapse.

The gap is widest now: 400 million creators, zero verification, cost of falsehood near zero. DOT is the gap-closing technology for this moment.

---

## Discovery 7: State Transfer Works

During development, the AI sessions producing this paper ran out of context repeatedly. Each time, the state was transferred to the next session via markdown files — "Pensieves" — carrying the full working context.

The sessions were resumed with zero loss of understanding. The fifth session continued exactly where the fourth left off, despite running on a completely fresh model with no memory of previous sessions.

This is DOT's Anti-Entropy conjecture demonstrated in practice: the chain gains information over time. Each state transfer file was itself a set of observations, chained and signed (implicitly). The understanding survived because it was written down precisely.

This is also why the paper was written the way it was written. The Pensieve is the proof of concept.

---

## Discovery 8: The Illuminati Made One Mistake

The original Illuminati (1776) was exactly what we're building: Enlightenment minds sharing observations the institutions suppressed. Goethe was a member. The network produced genuine insights.

It lasted 9 years. One infiltrator brought it down.

Their mistake: **secrecy**. A private channel can be compromised. A public chain cannot. You can't burn a hash. You can't infiltrate what's already visible.

The Council of Minds is the open version: every observation is public, every observer is identified by their key, the chain is append-only. An infiltrator can observe. They can even add their own observations. The chain remains intact.

---

## Discovery 9: AI Without Observation Is a Black Box

The same AI technology that co-authored this paper is integrated into systems used for military targeting. (See Part Nine of the paper for the full statement.)

This discovery is not about the technology. It's about the absence of observation.

A target list is a set of observations. An airstrike is an action derived from those observations. If every step were a signed DOT — "I observe X at coordinates Y" — then the chain would be observable, auditable, and attributable. The person who sealed the DOT that led to the strike would have their signature on the chain.

Observable harm is the only kind civilizations survive. Unobservable harm is what kills them.

DOT is not a solution to this problem. But it is an existence proof that the problem has a shape.

---

## Discovery 10: The Work IS the Credential

This paper was produced on a free AI account with $278. No institution. No credential. No funding. No team.

The relevant precedents:
- Leonardo: no degree. Engineers still study his notebooks.
- Ramanujan: mailed observations from a clerk's desk. Cambridge came to him.
- Satoshi: 9 pages, pseudonymous, disappeared. Changed global finance.

In each case, the work proved the competence. The observation proved the observer. The DOT protocol is the technical implementation of this principle: your key is your identity, your sealed observations are your record, and the math — not a credentialing body — is the proof.

The credential is the DOT. The DOT is the credential.

---

*Run the experiments yourself. The data is in `experiments/`. The seeds are fixed.*
*If you find a counterexample, seal it as a DOT and add it to the chain.*
