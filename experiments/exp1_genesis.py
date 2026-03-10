#!/usr/bin/env python3
"""
Experiment 1: Genesis DOT
Create and verify the genesis DOT.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dot_crypto import generate_keypair, pubkey_bytes
from dot_core import create_dot, parse_dot, verify_dot, TYPE_IDENTITY, GENESIS_PREV_HASH
from dot_chain import hash_dot

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run():
    # 1. Generate Ed25519 keypair
    signing_key, verify_key = generate_keypair()

    # 2. Save private key (raw hex, no PEM dependency)
    priv_path = os.path.join(BASE_DIR, "genesis_key.pem")
    pub_path  = os.path.join(BASE_DIR, "genesis_key.pub")

    priv_bytes = bytes(signing_key)
    with open(priv_path, 'w') as f:
        f.write("-----BEGIN ED25519 PRIVATE KEY-----\n")
        f.write(priv_bytes.hex() + "\n")
        f.write("-----END ED25519 PRIVATE KEY-----\n")

    # 3. Save public key as hex
    pub_hex = pubkey_bytes(verify_key).hex()
    with open(pub_path, 'w') as f:
        f.write(pub_hex + "\n")

    # 4. Create IDENTITY DOT (genesis)
    payload_text = "The act of observation leaves its dot."
    raw = create_dot(
        payload_text,
        signing_key,
        verify_key,
        dot_type=TYPE_IDENTITY,
        prev_hash=GENESIS_PREV_HASH,
    )

    # 5. Write genesis.dot
    genesis_path = os.path.join(BASE_DIR, "genesis.dot")
    with open(genesis_path, 'wb') as f:
        f.write(raw)

    # 6. Read back and verify
    with open(genesis_path, 'rb') as f:
        read_back = f.read()

    assert read_back == raw, "Read-back mismatch!"
    valid = verify_dot(read_back)
    parsed = parse_dot(read_back)

    # 7. Compute BLAKE3 hash
    h = hash_dot(raw).hex()

    # 8. Write hex dump file
    hex_path = os.path.join(BASE_DIR, "genesis.dot.hex")
    with open(hex_path, 'w') as f:
        f.write(raw.hex() + "\n")

    # Print results
    print(f"✓ genesis.dot created")
    print(f"Size: {len(raw)} bytes")
    print(f"BLAKE3 hash: {h}")
    print(f"Public key: {pub_hex}")
    print(f'Payload: "{parsed["payload"].decode("utf-8")}"')
    print(f"Signature valid: {valid}")
    print()
    print(f"Files written:")
    print(f"  {genesis_path}")
    print(f"  {priv_path}")
    print(f"  {pub_path}")
    print(f"  {hex_path}")

    assert valid, "Genesis DOT signature verification failed!"
    return raw, h, pub_hex


if __name__ == '__main__':
    run()
