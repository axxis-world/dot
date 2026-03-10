#!/usr/bin/env python3
"""
Experiment 3: Minimum Viable DOT
Find the minimum byte size of a valid DOT and compare to alternatives.
"""

import sys
import os
import json
import base64
import time
import struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dot_crypto import generate_keypair, pubkey_bytes, sign
from dot_core import create_dot, verify_dot, TYPE_OBSERVATION


def measure_jwt(payload_bytes: bytes, signing_key, verify_key) -> int:
    """Approximate JWT size for equivalent fields."""
    # JWT = base64url(header) + "." + base64url(payload) + "." + base64url(sig)
    # We simulate an EdDSA JWT manually
    import time as _time

    header = json.dumps({"alg": "EdDSA", "typ": "JWT"}).encode()
    body = json.dumps({
        "iat": int(_time.time()),
        "obs": payload_bytes.hex(),  # observer pubkey as string claim
        "v": 1
    }).encode()

    def b64url(b):
        return base64.urlsafe_b64encode(b).rstrip(b'=')

    h_enc = b64url(header)
    b_enc = b64url(body)
    signing_input = h_enc + b'.'+b_enc
    sig = sign(signing_input, signing_key)
    sig_enc = b64url(sig)
    jwt = signing_input + b'.' + sig_enc
    return len(jwt)


def measure_protobuf_estimate() -> int:
    """Estimate protobuf size for equivalent fields.
    Fields: version(1B), type(1B), timestamp(8B), pubkey(32B), prev_hash(32B),
            payload(1B), signature(64B)
    With protobuf field tags + length prefixes.
    Estimate for varint-encoded fields:
      field 1 (uint32 version=1): tag(1) + val(1) = 2
      field 2 (uint32 type=2): tag(1) + val(1) = 2
      field 3 (uint64 timestamp): tag(1) + val(~5) = 6
      field 4 (bytes pubkey 32B): tag(1) + len(1) + 32 = 34
      field 5 (bytes prev_hash 32B): tag(1) + len(1) + 32 = 34
      field 6 (bytes payload 1B): tag(1) + len(1) + 1 = 3
      field 7 (bytes signature 64B): tag(1) + len(1) + 64 = 66
    Total: 2+2+6+34+34+3+66 = 147 bytes
    """
    return 147


def measure_json_sig(payload_bytes: bytes, signing_key) -> int:
    """Measure JSON + separate signature size."""
    import time as _time
    pub = bytes(signing_key.verify_key).hex()
    obj = {
        "version": 1,
        "type": "observation",
        "timestamp": int(_time.time() * 1_000_000),
        "observer": pub,
        "prev_hash": "0" * 64,
        "payload": payload_bytes.hex(),
    }
    json_bytes = json.dumps(obj, separators=(',', ':')).encode()
    sig = sign(json_bytes, signing_key)
    sig_b64 = base64.b64encode(sig).decode()
    envelope = json.dumps({"dot": json.loads(json_bytes), "sig": sig_b64},
                          separators=(',', ':')).encode()
    return len(envelope)


def run():
    signing_key, verify_key = generate_keypair()

    # 1. Minimum valid DOT: 1-byte payload, no TLVs
    min_payload = b'\x00'
    raw = create_dot(min_payload, signing_key, verify_key, dot_type=TYPE_OBSERVATION)
    assert verify_dot(raw), "Minimum DOT failed verification!"

    dot_size = len(raw)

    # Breakdown
    header_size  = 10
    body_fixed   = 8 + 32 + 32 + 4  # timestamp + observer + prev_hash + payload_len
    payload_size = 1
    sig_size     = 64
    expected_total = header_size + body_fixed + payload_size + sig_size
    assert dot_size == expected_total, f"Size mismatch: {dot_size} vs {expected_total}"

    # 2. Comparison formats
    jwt_size   = measure_jwt(min_payload, signing_key, verify_key)
    proto_size = measure_protobuf_estimate()
    json_size  = measure_json_sig(min_payload, signing_key)
    bitcoin_tx = 191  # known minimum Bitcoin transaction (P2PKH)

    # 3. Print comparison table
    print("Minimum DOT Size Comparison")
    print("─" * 68)
    print(f"{'Format':<20} {'Min Size':>10}   {'Self-Desc?':<12} {'Offline?'}")
    print("─" * 68)
    print(f"{'DOT':<20} {dot_size:>6} bytes   {'Yes':<12} Yes")
    print(f"{'JWT':<20} {jwt_size:>6} bytes   {'Yes (header)':<12} No (alg needed)")
    print(f"{'Protobuf':<20} {proto_size:>6} bytes   {'No':<12} Yes")
    print(f"{'JSON+signature':<20} {json_size:>6} bytes   {'Partial':<12} Yes")
    print(f"{'Bitcoin tx':<20} {bitcoin_tx:>6} bytes   {'No':<12} No")
    print("─" * 68)

    # Determine winner
    sizes = [
        ("DOT", dot_size),
        ("Protobuf", proto_size),
        ("JWT", jwt_size),
        ("JSON+sig", json_size),
        ("Bitcoin", bitcoin_tx),
    ]
    winner = min(sizes, key=lambda x: x[1])
    print(f"Smallest: {winner[0]} ({winner[1]} bytes)")
    print()

    # Detailed DOT breakdown
    print(f"DOT Breakdown ({dot_size} bytes):")
    print(f"  Header:      {header_size} bytes  (magic + version + suite + flags + type + tlv_count)")
    print(f"  Timestamp:   8 bytes  (uint64 µs)")
    print(f"  Observer:   32 bytes  (Ed25519 pubkey)")
    print(f"  Prev hash:  32 bytes  (BLAKE3)")
    print(f"  Payload len: 4 bytes  (uint32)")
    print(f"  Payload:     {payload_size} byte   (minimum)")
    print(f"  Signature:  64 bytes  (Ed25519)")
    print(f"  ─────────────────────")
    print(f"  Total:     {dot_size} bytes")

    print()
    print(f"✓ Minimum valid DOT verified: {dot_size} bytes")

    return dot_size


if __name__ == '__main__':
    run()
