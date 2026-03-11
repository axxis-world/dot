# Experiment Results

All experiments are deterministic. Run them yourself:

```bash
pip install pynacl blake3
python experiments/exp1_genesis.py
python experiments/exp2_integrity.py
python experiments/exp3_minimum.py
python experiments/exp4_cold_open.py
```

---

## Experiment 1: Genesis DOT

**Source:** `exp1_genesis.py`
**Purpose:** Create the genesis DOT — the first observation in a new chain.

**Result:**
```
✓ genesis.dot created
Size: 196 bytes
BLAKE3 hash: ef31d25e4b553e638c86ccd76617e247ff1c612fa04ff92467343d8c089bdf26
Public key: 2a993b4c4ce7146699c2e769994f002cf8276eb07e4b92b229ac74851baa0576
Payload: "The act of observation leaves its dot."
Signature valid: True
```

**Files produced:**
- `genesis.dot` — the binary DOT file (196 bytes)
- `genesis.dot.hex` — hex dump
- `genesis_key.pub` — observer public key (hex)

**Observation:** The genesis DOT's `prev_hash` is 32 zero bytes — the sentinel value indicating this is the first observation in a new chain. Every subsequent DOT in a chain must set `prev_hash` to the BLAKE3 hash of the previous DOT.

---

## Experiment 2: Integrity Prism

**Source:** `exp2_integrity.py`
**Purpose:** Prove 100% tamper detection across four tamper strategies.

**Setup:** 1,000 DOTs created with random payloads (seed=42, deterministic). 100 DOTs tampered:
- 25 × payload flip (1 bit changed anywhere in payload)
- 25 × timestamp modification (1 byte of timestamp changed)
- 25 × signature alteration (1 byte of signature changed)
- 25 × prev_hash swap (all 32 bytes replaced with random data)

**Result:**
```
Total DOTs: 1000
Valid DOTs: 900
Tampered DOTs: 100
Detected: 100/100 (100.0%)
False positives: 0

Breakdown:
  Payload flip:     25/25 detected
  Timestamp mod:    25/25 detected
  Signature alter:  25/25 detected
  Prev_hash swap:   25/25 detected

Avg verification time: 0.06ms per DOT
✓ All assertions passed — 100% tamper detection, 0 false positives
```

**Observation:** Ed25519 covers the entire signable region (header + body). Any bit flip anywhere in the signed region produces a signature verification failure. The signature is not "mostly over" the content — it is over all of it.

The verification time (0.06ms per DOT) means a single machine can verify ~16,000 DOTs per second. A chain of 1 billion observations can be fully verified in ~17 hours on one core.

---

## Experiment 3: Minimum Viable DOT

**Source:** `exp3_minimum.py`
**Purpose:** Find the minimum byte size and compare to alternative formats.

**Result:**
```
Minimum DOT Size Comparison
────────────────────────────────────────────────────────────────────
Format               Min Size   Self-Desc?   Offline?
────────────────────────────────────────────────────────────────────
DOT                   151 bytes   Yes          Yes
JWT                  ~182 bytes   Yes (header) No (alg needed)
Protobuf             ~147 bytes   No           Yes
JSON+signature       ~280 bytes   Partial      Yes
Bitcoin tx            191 bytes   No           No
────────────────────────────────────────────────────────────────────
Smallest: Protobuf (147 bytes)

DOT Breakdown (151 bytes):
  Header:      10 bytes  (magic + version + suite + flags + type + tlv_count)
  Timestamp:    8 bytes  (uint64 µs)
  Observer:    32 bytes  (Ed25519 pubkey)
  Prev hash:   32 bytes  (BLAKE3)
  Payload len:  4 bytes  (uint32)
  Payload:      1 byte   (minimum)
  Signature:   64 bytes  (Ed25519)
  ─────────────────────
  Total:       151 bytes

✓ Minimum valid DOT verified: 151 bytes
```

**Observation:** Protobuf is 4 bytes smaller, but it requires a `.proto` schema file to parse — it is not self-describing. DOT at 151 bytes is the smallest self-describing, chain-linked, offline-verifiable signed observation format measured.

JWT at 182 bytes cannot be verified offline — you need the algorithm context and potentially a JWKS endpoint.

Bitcoin's minimum transaction at 191 bytes requires UTXO state to verify — it is not standalone.

DOT is standalone. Give someone a DOT file and the public key. That's it.

---

## Experiment 4: Cold Open / Hex Dump

**Source:** `exp4_cold_open.py`
**Purpose:** Prove the format is self-describing — parseable with no prior documentation.

**The annotated hex dump (from `cold_open_annotated.txt`):**

```
Offset  Hex (16 bytes)                                    ASCII             Annotation
────────────────────────────────────────────────────────────────────────────────────────
00000000  89 44 4f 54 01 01 00 00 02 00 00 06 4c ac df 2d  .DOT........L..-  [0] HEADER: magic=\x89DOT
00000010  74 70 1f 23 35 57 c1 6d 3e de 16 2f 45 6c 56 5f  tp.#5W.m>../ElV_  [18] BODY: observer (Ed25519 pubkey, 32 bytes)
00000020  06 ac 3d 28 6c 38 6a 18 2c 36 b6 5e f8 97 39 9d  ..=(l8j.,6.^..9.
00000030  3a 1e 00 00 00 00 00 00 00 00 00 00 00 00 00 00  :...............  [50] BODY: prev_hash (genesis — all zeros)
00000040  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
00000050  00 00 00 00 00 2d 4f 62 73 65 72 76 61 74 69 6f  .....-Observatio  [82] BODY: payload_len=45
00000060  6e 20 69 73 20 74 68 65 20 66 69 72 73 74 20 61  n is the first a
00000070  63 74 20 6f 66 20 74 68 65 20 75 6e 69 76 65 72  ct of the univer
00000080  73 65 2e 18 b8 91 95 6b 28 ec 6d 44 8b be a9 70  se.....k(.mD...p  [131] SIGNATURE: Ed25519 (64 bytes)
00000090  03 d5 ab 17 c3 27 cc 94 69 19 a0 18 9b 64 c3 89  .....'..i....d..
000000a0  f1 ff 15 26 f2 47 a1 0d 85 af bc 07 26 38 04 46  ...&.G......&8.F
000000b0  8c 52 da 4f 33 ef 70 96 61 c4 7e ed f3 5d 94 b2  .R.O3.p.a.~..]..
000000c0  d6 c6 03                                         ...
```

**Field identification from cold:**

| What you see | What it means |
|---|---|
| `89 44 4f 54` at offset 0 | Magic bytes. `\x89` prevents text detection. `DOT` = format name. |
| `01` at offset 4 | Version 1. |
| `01` at offset 5 | Crypto suite 1 = Ed25519 + BLAKE3. |
| `00 00` at offset 6 | Flags = 0 (unencrypted, no chain extension). |
| `02` at offset 8 | Type = OBSERVATION (0x02). |
| `00 06 4c ac df 2d 74 70` at offset 10 | Timestamp µs. Decodes to a recognizable date. |
| 32 bytes of random-looking data at offset 18 | Ed25519 public key. |
| 32 zero bytes at offset 50 | prev_hash = genesis (no previous DOT). |
| `00 00 00 2d` at offset 82 | payload_len = 45 bytes. |
| ASCII text "Observation is the first act..." at offset 86 | The payload. Readable directly. |
| 64 bytes at the end | Ed25519 signature. |

**Observation:** A programmer with a hex editor and knowledge of Ed25519 key sizes can parse this file without any documentation. The magic bytes lead to the format name. The format name leads to this spec. The spec leads to a verifier. This is the self-describing property.

Compare to a Protobuf file: without the `.proto` file, the hex dump is uninterpretable.

---

## Running All Experiments

```bash
git clone https://github.com/axxis-world/dot.git
cd dot
pip install pynacl blake3
python experiments/exp1_genesis.py
python experiments/exp2_integrity.py
python experiments/exp3_minimum.py
python experiments/exp4_cold_open.py
```

Expected total runtime: < 5 seconds. All results are deterministic.

If your results differ, open an issue with your Python version, OS, and pynacl/blake3 versions.
