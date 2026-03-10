"""
dot_chain.py — BLAKE3 hashing and chain utilities for DOT protocol.
"""

import blake3
from dot_core import create_dot, parse_dot

GENESIS_HASH = b'\x00' * 32


def hash_dot(raw_dot: bytes) -> bytes:
    """Compute the BLAKE3 hash of a raw DOT. Returns 32 bytes."""
    return blake3.blake3(raw_dot).digest()


def create_chain_dot(payload: str, signing_key, verify_key, prev_dot: bytes) -> bytes:
    """Create a new DOT chained to prev_dot via its BLAKE3 hash."""
    prev_hash = hash_dot(prev_dot)
    return create_dot(payload, signing_key, verify_key, prev_hash=prev_hash)


def verify_chain(dots: list) -> bool:
    """Verify an ordered list of DOTs form a valid hash chain.
    Checks each dot's prev_hash matches the BLAKE3 hash of the previous dot.
    The first dot must have genesis prev_hash (all zeros) or any valid prev_hash.
    Returns True if the chain is intact, False otherwise.
    """
    for i in range(1, len(dots)):
        parsed = parse_dot(dots[i])
        expected_prev = hash_dot(dots[i - 1])
        if parsed['prev_hash'] != expected_prev:
            return False
    return True
