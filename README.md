# DOT Protocol — Reference Implementation

The DOT format is a cryptographically signed, hash-linked observation.
Two operations: SEAL and OPEN. Five library functions.

## The Wire Format

Every DOT is composed of four sections:

1. **HEADER** (10 bytes) — Magic `\x89DOT`, version, crypto suite, flags, type, TLV count
2. **TLV EXTENSIONS** (variable, 0 bytes for minimal DOT) — Optional extension fields
3. **BODY** (variable) — Timestamp (8B), observer pubkey (32B), prev_hash (32B), payload_len (4B), payload
4. **SIGNATURE** (64 bytes) — Ed25519 signature over header + TLV + body

```
[HEADER 10B][TLVs 0+B][timestamp 8B][observer 32B][prev_hash 32B][payload_len 4B][payload NB][sig 64B]
```

Minimum valid DOT: **151 bytes** (1-byte payload).

## Usage

```bash
python dot_cli.py genesis                        # Create genesis.dot
python dot_cli.py seal "My observation"          # Seal text as observation.dot
python dot_cli.py open observation.dot           # Inspect and verify a DOT
```

## Library

```python
from dot_core import create_dot, parse_dot, verify_dot
from dot_crypto import generate_keypair
from dot_chain import hash_dot, create_chain_dot, verify_chain

signing_key, verify_key = generate_keypair()
raw = create_dot("My observation", signing_key, verify_key)
print(verify_dot(raw))   # True
print(parse_dot(raw))    # All fields as dict
```

## Experiments

Run all four in order:

```bash
python experiments/exp1_genesis.py   # Creates genesis.dot — the founding observation
python experiments/exp2_integrity.py # 1000 DOTs, 100 tampered — proves 100% detection
python experiments/exp3_minimum.py   # Finds minimum byte size (151 bytes)
python experiments/exp4_cold_open.py # Generates annotated hex dump for cold analysis
```

### Results

| Experiment | Result |
|---|---|
| Exp 1: Genesis | 188-byte IDENTITY DOT created and verified |
| Exp 2: Integrity | 100/100 tampered DOTs detected, 0 false positives, ~0.57ms/DOT |
| Exp 3: Minimum | 151 bytes — smaller than JWT (182B), Bitcoin tx (191B), JSON+sig (340B) |
| Exp 4: Cold Open | Full annotated hex dump generated |

## genesis.dot

The founding observation: `"The act of observation leaves its dot."`

Hash: `f34b74500250cf8ac5ccd598ff2b816067673c1759f775a1002a121d331c03e8`

188 bytes. Type: IDENTITY. Prev_hash: 32 zero bytes (genesis).

The chain continues.

## Crypto

- Signing: Ed25519 (pynacl)
- Hashing: BLAKE3 (for chain linking)
- Planned: X25519 key exchange + AES-256-GCM for encrypted DOTs (crypto suite 0x01)

## Wire Format Constants

```python
DOT_MAGIC        = b'\x89DOT'   # 0x89, 0x44, 0x4F, 0x54
TYPE_IDENTITY    = 0x01
TYPE_OBSERVATION = 0x02
TYPE_ENCRYPTED   = 0x03
TYPE_CHAIN       = 0x04
FLAG_ENCRYPTED   = 0x0001
FLAG_HAS_CHAIN   = 0x0002
```
