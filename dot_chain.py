"""
dot_chain.py — BLAKE3 hashing and chain utilities for the DOT protocol.

The chain is formed by BLAKE3-hashing each complete DOT (all bytes: header +
TLVs + body + signature) and storing that hash in the next DOT's prev_hash field.

    DOT₁: prev_hash = b'\\x00' * 32   (genesis sentinel)
    DOT₂: prev_hash = BLAKE3(DOT₁)
    DOT₃: prev_hash = BLAKE3(DOT₂)

A single-bit change to any DOT breaks every prev_hash link that follows it.
There is no way to modify history without regenerating every subsequent signature.
"""

import blake3
from dot_core import create_dot, parse_dot

GENESIS_HASH = b'\x00' * 32


def hash_dot(raw_dot: bytes) -> bytes:
    """Compute the BLAKE3 hash of a complete raw DOT.

    Hashes all bytes: header + TLV extensions + body + signature.
    The result is used as prev_hash in the next DOT in the chain.

    Args:
        raw_dot: complete serialized DOT bytes

    Returns:
        32-byte BLAKE3 digest
    """
    return blake3.blake3(raw_dot).digest()


def create_chain_dot(payload: str, signing_key, verify_key, prev_dot: bytes) -> bytes:
    """Create a new OBSERVATION DOT chained to prev_dot.

    Computes BLAKE3(prev_dot) and sets it as the new DOT's prev_hash,
    forming a tamper-evident link between the two observations.

    Args:
        payload:    observation text (str or bytes)
        signing_key: pynacl SigningKey
        verify_key:  pynacl VerifyKey matching signing_key
        prev_dot:   raw bytes of the immediately preceding DOT

    Returns:
        raw bytes of the new chained DOT
    """
    prev_hash = hash_dot(prev_dot)
    return create_dot(payload, signing_key, verify_key, prev_hash=prev_hash)


def verify_chain(dots: list) -> bool:
    """Verify that an ordered list of raw DOTs forms a valid hash chain.

    For each DOT at index i > 0, checks:
        parse(dots[i]).prev_hash == BLAKE3(dots[i-1])

    Does NOT verify Ed25519 signatures — call verify_dot() on each DOT
    individually for full cryptographic verification.

    Args:
        dots: list of raw DOT bytes in chain order (oldest first)

    Returns:
        True if all prev_hash links are intact, False if any link is broken.
        An empty list or single-element list always returns True.
    """
    for i in range(1, len(dots)):
        parsed = parse_dot(dots[i])
        expected_prev = hash_dot(dots[i - 1])
        if parsed['prev_hash'] != expected_prev:
            return False
    return True
