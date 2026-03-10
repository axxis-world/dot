"""
dot_crypto.py — Ed25519 key generation, signing, and verification for DOT protocol.
"""

import nacl.signing
import nacl.exceptions


def generate_keypair():
    """Generate a new Ed25519 keypair.
    Returns: (signing_key, verify_key) as pynacl objects.
    """
    signing_key = nacl.signing.SigningKey.generate()
    verify_key = signing_key.verify_key
    return signing_key, verify_key


def sign(message: bytes, signing_key) -> bytes:
    """Sign a message with an Ed25519 signing key.
    Returns: 64-byte signature.
    """
    signed = signing_key.sign(message)
    return signed.signature  # just the 64-byte sig, not the message


def verify(message: bytes, signature: bytes, verify_key) -> bool:
    """Verify an Ed25519 signature.
    Returns: True if valid, False otherwise.
    """
    try:
        verify_key.verify(message, signature)
        return True
    except nacl.exceptions.BadSignatureError:
        return False


def pubkey_bytes(verify_key) -> bytes:
    """Extract the raw 32-byte public key from a pynacl verify key."""
    return bytes(verify_key)


def signing_key_from_bytes(raw: bytes):
    """Reconstruct a SigningKey from 32 raw bytes."""
    return nacl.signing.SigningKey(raw)


def verify_key_from_bytes(raw: bytes):
    """Reconstruct a VerifyKey from 32 raw bytes."""
    return nacl.signing.VerifyKey(raw)
