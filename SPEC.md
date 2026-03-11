# DOT Wire Format Specification

Version 1.0 · March 2026

---

## Overview

A DOT is a cryptographically signed, hash-linked observation. Every byte has a defined purpose. The format is self-describing — a programmer with no prior documentation can parse `genesis.dot` from the magic bytes alone.

**Minimum valid DOT: 151 bytes** (1-byte payload, no TLV extensions)

---

## Wire Format

```
┌─────────────────────────────────────────────────────────┐
│  HEADER       10 bytes  Fixed                           │
│  TLV          variable  0 bytes for minimal DOT         │
│  BODY         variable  ≥76 bytes (8+32+32+4 + payload) │
│  SIGNATURE    64 bytes  Ed25519 over header+TLV+body     │
└─────────────────────────────────────────────────────────┘
```

---

## HEADER (10 bytes)

| Offset | Size | Field         | Value          | Description                        |
|--------|------|---------------|----------------|------------------------------------|
| 0      | 4    | `magic`       | `\x89DOT`      | Format identifier. `\x89` prevents accidental text display. |
| 4      | 1    | `version`     | `0x01`         | Format version. Increment on breaking changes. |
| 5      | 1    | `crypto_suite`| `0x01`         | `0x01` = Ed25519 + X25519 + AES-256-GCM |
| 6      | 2    | `flags`       | big-endian u16 | Bit 0: encrypted. Bit 1: has-chain. Bits 2–15: reserved. |
| 8      | 1    | `type`        | `0x01`–`0x04`  | DOT type (see Types table below)   |
| 9      | 1    | `tlv_count`   | `0x00`–`0xFF`  | Number of TLV extension fields     |

### Magic Bytes

`\x89DOT` (hex: `89 44 4f 54`) was chosen by analogy with PNG (`\x89PNG`):
- `\x89` (0x89 > 127): fails ASCII text checks, prevents the file from being treated as plaintext
- `DOT`: human-readable format identifier
- Together: self-annotating. Any hex editor shows `.DOT` at offset 0.

### DOT Types

| Value  | Name          | Description                                 |
|--------|---------------|---------------------------------------------|
| `0x01` | `IDENTITY`    | Genesis / keypair identity declaration      |
| `0x02` | `OBSERVATION` | Standard signed observation                 |
| `0x03` | `ENCRYPTED`   | AES-256-GCM encrypted payload               |
| `0x04` | `CHAIN`       | Links to an external chain                  |

### Crypto Suites

| Value  | Signing  | Encryption   | Hashing | Notes                  |
|--------|----------|--------------|---------|------------------------|
| `0x01` | Ed25519  | X25519+AES   | BLAKE3  | Current default        |
| `0x02` | ML-DSA   | ML-KEM+AES   | SHA-3   | Post-quantum (planned) |

Upgrading from `0x01` to `0x02` is a **one-byte change** to the header. Old DOTs remain valid; a mixed-suite chain is legal.

---

## TLV EXTENSIONS (variable)

Present only when `tlv_count > 0`. Each extension:

| Offset | Size | Field    | Description                |
|--------|------|----------|----------------------------|
| +0     | 2    | `tag`    | Extension type (big-endian u16) |
| +2     | 2    | `length` | Value length in bytes (big-endian u16) |
| +4     | N    | `value`  | Extension-specific data    |

Reserved tags (not yet assigned):

| Tag    | Name         | Purpose                        |
|--------|--------------|--------------------------------|
| `0x01` | `GEOLOC`     | Lat/lon at observation time    |
| `0x02` | `MEDIA_HASH` | BLAKE3 of attached media file  |
| `0x03` | `REPLY_TO`   | Hash of DOT being replied to   |
| `0x04` | `THREAD_ID`  | Chain sub-thread identifier    |

---

## BODY (variable, ≥76 bytes)

| Offset   | Size | Field          | Type         | Description                      |
|----------|------|----------------|--------------|----------------------------------|
| 0        | 8    | `timestamp`    | uint64 BE    | Microseconds since Unix epoch    |
| 8        | 32   | `observer`     | bytes        | Ed25519 public key               |
| 40       | 32   | `prev_hash`    | bytes        | BLAKE3 hash of previous DOT. All zeros = genesis. |
| 72       | 4    | `payload_len`  | uint32 BE    | Payload length in bytes          |
| 76       | N    | `payload`      | bytes        | The observation. Any encoding.   |

**Body offset is relative to start of BODY section** (i.e., after header + all TLVs).

### Timestamp

Microseconds since Unix epoch, big-endian uint64. Range: 1970 to year 586,524. At 1 µs resolution, two observers cannot produce the same timestamp in practice, providing natural tie-breaking in chain ordering.

### Observer

Raw 32-byte Ed25519 public key. Not base58, not PEM. The key IS the identity — no certificate, no account, no email.

### Prev Hash

BLAKE3 hash of the previous DOT's entire raw bytes (header + TLVs + body + signature). Genesis DOTs use 32 zero bytes:

```
prev_hash = b'\x00' * 32  # genesis sentinel
```

### Payload

Arbitrary bytes. The format places no restriction on encoding. Implementations SHOULD use UTF-8 text for human-readable observations. The `payload_len` field allows binary payloads including images, JSON, or encrypted data.

**Encoding convention for named observations (WebDOT):**

```json
{"n": "Observer Name", "t": "The observation text"}
```

The name is cryptographically bound — it is inside the signed body. It cannot be changed after sealing without invalidating the signature.

---

## SIGNATURE (64 bytes)

Ed25519 signature over the concatenation of: `header + TLVs + body`

```
signable = header_bytes + tlv_bytes + body_bytes
signature = ed25519_sign(signable, signing_key)  # 64 bytes
```

The signature is appended as the final 64 bytes of the DOT. It is NOT included in `signable`.

---

## Size Breakdown

Minimum DOT (1-byte payload, 0 TLVs):

```
Header:       10 bytes   (magic + version + suite + flags + type + tlv_count)
Timestamp:     8 bytes   (uint64 µs)
Observer:     32 bytes   (Ed25519 pubkey)
Prev hash:    32 bytes   (BLAKE3)
Payload len:   4 bytes   (uint32)
Payload:       1 byte    (minimum)
Signature:    64 bytes   (Ed25519)
─────────────────────────
Total:       151 bytes
```

### Comparison Table

| Format         | Min Size | Self-Describing | Chain-Linked | Offline-Valid |
|----------------|----------|-----------------|--------------|---------------|
| **DOT**        | **151 B**| **Yes**         | **Yes**      | **Yes**       |
| JWT            | ~182 B   | Yes (header)    | No           | No (alg ctx)  |
| Protobuf       | ~147 B   | No (schema req) | No           | Yes           |
| JSON+signature | ~280 B   | Partial         | No           | Yes           |
| Bitcoin tx     | 191 B    | No              | Yes          | No (UTXO)     |

---

## Hash Chain

The chain is formed by BLAKE3-hashing each complete DOT and using that hash as `prev_hash` in the next DOT.

```
DOT₁: prev_hash = 0x00…00 (genesis)
DOT₂: prev_hash = BLAKE3(DOT₁ raw bytes)
DOT₃: prev_hash = BLAKE3(DOT₂ raw bytes)
…
```

Chain verification: for each DOT at index i > 0, `parse(DOTᵢ).prev_hash == BLAKE3(DOTᵢ₋₁)`. A single-bit change anywhere in DOTᵢ₋₁ produces a completely different BLAKE3 hash and breaks all subsequent links.

---

## WebDOT — Browser Implementation

The server-side chain (axxis.world) uses a simplified JSON representation for WebCrypto compatibility:

```json
{
  "timestamp": 1773171415040,
  "observer": "2a993b4c…",
  "prevHash": "0000…0000",
  "payload": "I am a child of the universe.",
  "signature": "1711443…",
  "hash": "ef31d25e…"
}
```

Key differences from the binary format:
- Hashing uses SHA-256 (WebCrypto available in all browsers) instead of BLAKE3
- Timestamp is milliseconds (JS `Date.now()`) instead of microseconds
- Fields are hex strings instead of raw bytes
- `hash` is the SHA-256 of the canonical JSON (sorted keys, no whitespace)

The formats are interoperable at the semantic level. A WebDOT can be translated to binary format by an implementation that has access to both.

---

## Self-Description

A programmer encountering a DOT file cold can determine:

1. **It's a DOT**: magic bytes `\x89DOT` at offset 0
2. **The version**: byte 4
3. **The crypto**: byte 5 (`0x01` = Ed25519+BLAKE3)
4. **The type**: byte 8 (IDENTITY, OBSERVATION, etc.)
5. **When it was created**: bytes 10–17 (timestamp_us)
6. **Who created it**: bytes 18–49 (Ed25519 pubkey)
7. **What it links to**: bytes 50–81 (prev_hash; all-zeros = genesis)
8. **What it says**: bytes 86+ (payload after the 4-byte length field)
9. **Verify it**: the last 64 bytes are the signature over everything above

No external schema. No registry. No network connection required.

---

## Future Extensions

The TLV system allows extending the format without breaking existing parsers. Any parser that encounters an unknown TLV tag SHOULD skip it (skip `length` bytes) and continue parsing. A parser that cannot handle a required TLV SHOULD reject the DOT but log the unknown tag.

Planned extensions:
- `0x01 GEOLOC`: lat/lon for physical observation provenance
- `0x02 MEDIA_HASH`: attach images, audio, or other binary content by hash reference
- `0x03 REPLY_TO`: threaded conversations in the chain
- `0x10 AI_MODEL`: which model co-created the observation (for AI-signed DOTs)

---

*This specification is public domain. Implement freely.*
