#!/usr/bin/env python3
"""
dot_cli.py — CLI for the DOT protocol.

Usage:
    python dot_cli.py seal "My observation"     # create observation.dot
    python dot_cli.py open observation.dot       # inspect a .dot file
    python dot_cli.py genesis                    # create genesis.dot
"""

import sys
import os
import datetime
from dot_core import create_dot, parse_dot, verify_dot, TYPE_IDENTITY, TYPE_OBSERVATION, GENESIS_PREV_HASH
from dot_crypto import generate_keypair, pubkey_bytes
from dot_chain import hash_dot

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_or_generate_keypair(key_prefix="default"):
    """Load existing keypair from disk or generate a new one."""
    priv_path = os.path.join(BASE_DIR, f"{key_prefix}_key.raw")
    pub_path  = os.path.join(BASE_DIR, f"{key_prefix}_key.pub")

    if os.path.exists(priv_path):
        from dot_crypto import signing_key_from_bytes
        with open(priv_path, 'rb') as f:
            raw = bytes.fromhex(f.read().strip().decode())
        signing_key = signing_key_from_bytes(raw)
        verify_key = signing_key.verify_key
    else:
        signing_key, verify_key = generate_keypair()
        with open(priv_path, 'w') as f:
            f.write(bytes(signing_key).hex())
        with open(pub_path, 'w') as f:
            f.write(pubkey_bytes(verify_key).hex())
        print(f"Generated new keypair → {priv_path}")

    return signing_key, verify_key


def cmd_seal(text: str, output_path: str = None):
    """Seal text as an OBSERVATION DOT."""
    signing_key, verify_key = _load_or_generate_keypair()
    raw = create_dot(text, signing_key, verify_key, dot_type=TYPE_OBSERVATION)

    if output_path is None:
        output_path = os.path.join(BASE_DIR, "observation.dot")

    with open(output_path, 'wb') as f:
        f.write(raw)

    h = hash_dot(raw).hex()
    print(f"Sealed → {output_path}")
    print(f"Size: {len(raw)} bytes")
    print(f"BLAKE3: {h}")
    return output_path


def cmd_open(dot_path: str):
    """Open and inspect a .dot file."""
    with open(dot_path, 'rb') as f:
        raw = f.read()

    valid = verify_dot(raw)
    parsed = parse_dot(raw)

    h = hash_dot(raw).hex()
    ts = parsed['timestamp_us']
    dt = datetime.datetime.fromtimestamp(ts / 1_000_000, tz=datetime.timezone.utc)

    status = "VALID" if valid else "INVALID"
    print(f"{'='*50}")
    print(f"DOT: {os.path.basename(dot_path)}")
    print(f"{'='*50}")
    print(f"Status:       {status}")
    print(f"Type:         {parsed['dot_type_name']} (0x{parsed['dot_type']:02x})")
    print(f"Version:      {parsed['version']}")
    print(f"Crypto suite: {parsed['crypto_suite']}")
    print(f"Flags:        0x{parsed['flags']:04x}")
    print(f"Timestamp:    {ts} µs")
    print(f"             ({dt.isoformat()})")
    print(f"Observer:     {parsed['observer'].hex()}")
    print(f"Prev hash:    {parsed['prev_hash'].hex()}")
    print(f"Payload ({parsed['payload_len']}B): {parsed['payload'].decode('utf-8', errors='replace')!r}")
    print(f"Signature:    {parsed['signature'].hex()[:32]}...")
    print(f"BLAKE3 hash:  {h}")
    print(f"Total size:   {parsed['total_size']} bytes")
    print(f"{'='*50}")

    return valid


def cmd_genesis():
    """Create genesis.dot — the founding DOT."""
    signing_key, verify_key = _load_or_generate_keypair("genesis")

    payload = "The act of observation leaves its dot."
    raw = create_dot(
        payload,
        signing_key,
        verify_key,
        dot_type=TYPE_IDENTITY,
        prev_hash=GENESIS_PREV_HASH,
    )

    genesis_path = os.path.join(BASE_DIR, "genesis.dot")
    with open(genesis_path, 'wb') as f:
        f.write(raw)

    h = hash_dot(raw).hex()
    pub = pubkey_bytes(verify_key).hex()

    print(f"✓ genesis.dot created")
    print(f"Size: {len(raw)} bytes")
    print(f"BLAKE3 hash: {h}")
    print(f"Public key: {pub}")
    print(f"Payload: {payload!r}")
    print(f"Signature valid: {verify_dot(raw)}")

    return genesis_path


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'seal':
        if len(sys.argv) < 3:
            print("Usage: python dot_cli.py seal \"text\"")
            sys.exit(1)
        cmd_seal(sys.argv[2])

    elif cmd == 'open':
        if len(sys.argv) < 3:
            print("Usage: python dot_cli.py open <file.dot>")
            sys.exit(1)
        valid = cmd_open(sys.argv[2])
        sys.exit(0 if valid else 1)

    elif cmd == 'genesis':
        cmd_genesis()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
