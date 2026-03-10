#!/usr/bin/env python3
"""
Experiment 4: Cold Open / Hex Dump
Generate a formatted hex dump of a DOT for cold analysis — no prior knowledge needed.
"""

import sys
import os
import datetime
import struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dot_crypto import generate_keypair
from dot_core import (create_dot, parse_dot, verify_dot, TYPE_OBSERVATION,
                      DOT_MAGIC, TYPE_NAMES, GENESIS_PREV_HASH)
from dot_chain import hash_dot

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def hex_dump_annotated(raw: bytes, parsed: dict) -> str:
    """Generate an annotated hex dump with 16 bytes per line."""
    lines = []

    def annotation_for_offset(offset: int, end: int) -> str:
        """Return annotation label for a byte range."""
        return ""  # populated per-line below

    # Build a mapping: offset -> annotation
    anns = {}
    # Header annotations
    anns[0]  = "HEADER: magic=\\x89DOT"
    anns[4]  = f"HEADER: version={parsed['version']}"
    anns[5]  = f"HEADER: crypto_suite={parsed['crypto_suite']} (Ed25519+X25519+AES-256-GCM)"
    anns[6]  = f"HEADER: flags=0x{parsed['flags']:04x} (unencrypted, no chain)"
    anns[8]  = f"HEADER: type=0x{parsed['dot_type']:02x} ({parsed['dot_type_name']})"
    anns[9]  = f"HEADER: tlv_count={parsed['tlv_count']}"

    # Body annotations
    ts_offset = 10
    anns[ts_offset] = f"BODY: timestamp={parsed['timestamp_us']}µs"

    obs_offset = ts_offset + 8
    anns[obs_offset] = f"BODY: observer (Ed25519 pubkey, 32 bytes)"

    prev_offset = obs_offset + 32
    anns[prev_offset] = f"BODY: prev_hash (BLAKE3, 32 bytes) = genesis (all zeros)"

    plen_offset = prev_offset + 32
    anns[plen_offset] = f"BODY: payload_len={parsed['payload_len']}"

    payload_offset = plen_offset + 4
    try:
        payload_text = parsed['payload'].decode('utf-8')
    except Exception:
        payload_text = repr(parsed['payload'])
    anns[payload_offset] = f'BODY: payload="{payload_text}"'

    sig_offset = payload_offset + parsed['payload_len']
    anns[sig_offset] = f"SIGNATURE: Ed25519 (64 bytes)"

    # Generate hex dump
    lines.append(f"{'Offset':>8}  {'Hex (16 bytes)':48}  {'ASCII':16}  Annotation")
    lines.append("─" * 120)

    for line_start in range(0, len(raw), 16):
        chunk = raw[line_start:line_start+16]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        # Pad hex part to consistent width (16*3-1 = 47 chars)
        hex_part = f'{hex_part:<47}'
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        ascii_part = f'{ascii_part:<16}'

        # Find annotation for this line
        ann = ""
        for offset in range(line_start, line_start + 16):
            if offset in anns:
                ann = f"[{offset}] {anns[offset]}"
                break

        lines.append(f"{line_start:08x}  {hex_part}  {ascii_part}  {ann}")

    return '\n'.join(lines)


def run():
    signing_key, verify_key = generate_keypair()

    payload_text = "Observation is the first act of the universe."
    raw = create_dot(
        payload_text,
        signing_key,
        verify_key,
        dot_type=TYPE_OBSERVATION,
        prev_hash=GENESIS_PREV_HASH,
    )

    assert verify_dot(raw), "Cold open DOT failed verification!"

    parsed = parse_dot(raw)
    h = hash_dot(raw).hex()

    # 1. Write plain hex file
    cold_hex_path = os.path.join(BASE_DIR, "cold_open.hex")
    with open(cold_hex_path, 'w') as f:
        f.write(raw.hex() + "\n")

    # 2. Write annotated dump
    dump = hex_dump_annotated(raw, parsed)
    cold_ann_path = os.path.join(BASE_DIR, "cold_open_annotated.txt")
    with open(cold_ann_path, 'w') as f:
        f.write(dump + "\n")

    # 3. Compute offsets
    payload_offset = 10 + 8 + 32 + 32 + 4  # header + ts + observer + prev_hash + payload_len
    sig_offset = payload_offset + parsed['payload_len']

    ts = parsed['timestamp_us']
    dt = datetime.datetime.fromtimestamp(ts / 1_000_000, tz=datetime.timezone.utc)

    # 4. Print cold open summary
    print("Cold Open Test — DOT Hex Dump")
    print("══════════════════════════════")
    print("What a naive parser should identify:")
    print(f"  [0-3]     Magic bytes: 0x{raw[0:4].hex().upper()} → \"\\x89DOT\"")
    print(f"  [4]       Version: 0x{raw[4]:02x}")
    print(f"  [5]       Crypto suite: 0x{raw[5]:02x} (1=Ed25519+X25519+AES-256-GCM)")
    print(f"  [6-7]     Flags: 0x{struct.unpack('>H', raw[6:8])[0]:04x} (unencrypted, no chain)")
    print(f"  [8]       Type: 0x{raw[8]:02x} ({TYPE_NAMES.get(raw[8], 'UNKNOWN')})")
    print(f"  [9]       TLV count: 0x{raw[9]:02x}")
    print(f"  [10-17]   Timestamp: {ts} = {dt.isoformat()}")
    print(f"  [18-49]   Observer public key (Ed25519, 32 bytes)")
    print(f"            {parsed['observer'].hex()[:32]}...")
    print(f"  [50-81]   Prev hash (BLAKE3, 32 bytes) = genesis (all zeros)")
    print(f"            {parsed['prev_hash'].hex()}")
    print(f"  [82-85]   Payload length: {parsed['payload_len']} bytes")
    print(f"  [86-{86+parsed['payload_len']-1}]   Payload (UTF-8): \"{payload_text}\"")
    print(f"  [{sig_offset}-{sig_offset+63}]  Ed25519 signature (64 bytes)")
    print(f"            {parsed['signature'].hex()[:32]}...")
    print(f"  Total: {len(raw)} bytes")
    print()
    print(f"BLAKE3 hash: {h}")
    print(f"Signature valid: {verify_dot(raw)}")
    print()
    print(f"Files written:")
    print(f"  {cold_hex_path}")
    print(f"  {cold_ann_path}")
    print()
    print("── Annotated Hex Dump (first 6 lines) ──")
    for line in dump.split('\n')[:8]:
        print(line)
    print("...")

    return raw


if __name__ == '__main__':
    run()
