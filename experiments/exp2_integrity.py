#!/usr/bin/env python3
"""
Experiment 2: Integrity Prism
Create 1,000 DOTs, tamper with 100, verify all — prove 100% tamper detection.
"""

import sys
import os
import random
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dot_crypto import generate_keypair
from dot_core import create_dot, verify_dot, TYPE_OBSERVATION


def run():
    rng = random.Random(42)  # deterministic for reproducibility

    # 1. Generate keypair
    signing_key, verify_key = generate_keypair()

    # 2. Create 1,000 valid OBSERVATION DOTs with random 10-50 byte payloads
    print("Creating 1,000 DOTs...")
    dots = []
    for i in range(1000):
        length = rng.randint(10, 50)
        payload = bytes([rng.randint(32, 126) for _ in range(length)])  # printable ASCII
        raw = create_dot(payload, signing_key, verify_key, dot_type=TYPE_OBSERVATION)
        dots.append(bytearray(raw))

    # 3. Choose 100 random indices to tamper
    tamper_indices = rng.sample(range(1000), 100)
    tamper_sets = {
        'payload_flip': tamper_indices[0:25],
        'timestamp_mod': tamper_indices[25:50],
        'sig_alter': tamper_indices[50:75],
        'prevhash_swap': tamper_indices[75:100],
    }

    # Track which indices are tampered
    tampered_set = set(tamper_indices)
    tamper_type = {}
    for t, idxs in tamper_sets.items():
        for i in idxs:
            tamper_type[i] = t

    # Tamper each DOT in place
    for i in tamper_sets['payload_flip']:
        dot = dots[i]
        # Payload starts at offset: 10 (header) + 8 (ts) + 32 (pubkey) + 32 (prev_hash) + 4 (payload_len) = 86
        payload_offset = 86
        payload_len = (dot[82] << 24) | (dot[83] << 16) | (dot[84] << 8) | dot[85]
        if payload_len > 0:
            flip_pos = payload_offset + rng.randint(0, payload_len - 1)
            dot[flip_pos] ^= 0x01  # flip one bit

    for i in tamper_sets['timestamp_mod']:
        dot = dots[i]
        # Timestamp is at offset 10 (right after 10-byte header)
        dot[10] = (dot[10] + 1) & 0xFF

    for i in tamper_sets['sig_alter']:
        dot = dots[i]
        # Signature is the last 64 bytes
        sig_offset = len(dot) - 64
        alter_pos = sig_offset + rng.randint(0, 63)
        dot[alter_pos] ^= 0xFF

    for i in tamper_sets['prevhash_swap']:
        dot = dots[i]
        # prev_hash starts at offset 10+8+32 = 50
        prev_hash_offset = 50
        random_hash = bytes([rng.randint(0, 255) for _ in range(32)])
        dot[prev_hash_offset:prev_hash_offset+32] = random_hash

    # 4. Verify all 1,000 DOTs and time it
    print("Verifying all 1,000 DOTs...")
    start = time.perf_counter()
    results = [verify_dot(bytes(dot)) for dot in dots]
    elapsed = time.perf_counter() - start

    # 5. Analyze results
    valid_count = sum(results)
    invalid_count = 1000 - valid_count

    # Detected: tampered DOTs that were marked invalid
    detected = {i for i in tampered_set if not results[i]}
    false_positives = sum(1 for i in range(1000) if i not in tampered_set and not results[i])
    false_negatives = sum(1 for i in tampered_set if results[i])

    detected_by_type = {}
    for t, idxs in tamper_sets.items():
        detected_by_type[t] = sum(1 for i in idxs if not results[i])

    avg_ms = (elapsed / 1000) * 1000

    # 6. Print results
    print()
    print(f"Total DOTs: 1000")
    print(f"Valid DOTs: {valid_count}")
    print(f"Tampered DOTs: {len(tampered_set)}")
    print(f"Detected: {len(detected)}/100 ({len(detected)/100*100:.1f}%)")
    print(f"False positives: {false_positives}")
    print()
    print(f"Breakdown:")
    print(f"  Payload flip:     {detected_by_type['payload_flip']}/25 detected")
    print(f"  Timestamp mod:    {detected_by_type['timestamp_mod']}/25 detected")
    print(f"  Signature alter:  {detected_by_type['sig_alter']}/25 detected")
    print(f"  Prev_hash swap:   {detected_by_type['prevhash_swap']}/25 detected")
    print()
    print(f"Avg verification time: {avg_ms:.3f}ms per DOT")

    # Assertions
    assert len(detected) == 100, f"Expected 100 detected, got {len(detected)}"
    assert false_positives == 0, f"Expected 0 false positives, got {false_positives}"
    print()
    print("✓ All assertions passed — 100% tamper detection, 0 false positives")

    return results


if __name__ == '__main__':
    run()
