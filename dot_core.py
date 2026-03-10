"""
dot_core.py — Wire format serialization/deserialization for the DOT protocol.

WIRE FORMAT:
  HEADER (10 bytes):
    Magic:        4 bytes  \x89DOT
    Version:      1 byte   0x01
    Crypto suite: 1 byte   0x01 = Ed25519 + X25519 + AES-256-GCM
    Flags:        2 bytes  bit 0=encrypted, bit 1=has-chain, bits 2-15 reserved
    Type:         1 byte   0x01=IDENTITY, 0x02=OBSERVATION, 0x03=ENCRYPTED, 0x04=CHAIN
    TLV count:    1 byte   number of TLV extension fields

  TLV EXTENSIONS (variable, 0 for minimal DOT):
    Tag:    2 bytes
    Length: 2 bytes
    Value:  [Length] bytes

  BODY (variable):
    Timestamp:    8 bytes  uint64 microseconds since Unix epoch (big-endian)
    Observer:     32 bytes Ed25519 public key
    Prev_hash:    32 bytes BLAKE3 hash of previous DOT (0x00x32 for genesis)
    Payload_len:  4 bytes  uint32 big-endian
    Payload:      [Payload_len] bytes

  SIGNATURE (64 bytes):
    Ed25519 signature over everything above (header + TLV extensions + body)
"""

import struct
import time
from dot_crypto import sign, verify, pubkey_bytes

# Constants
DOT_MAGIC = b'\x89DOT'
DOT_VERSION = 0x01
CRYPTO_SUITE_ED25519 = 0x01

TYPE_IDENTITY    = 0x01
TYPE_OBSERVATION = 0x02
TYPE_ENCRYPTED   = 0x03
TYPE_CHAIN       = 0x04

FLAG_ENCRYPTED = 0x0001
FLAG_HAS_CHAIN = 0x0002

GENESIS_PREV_HASH = b'\x00' * 32

TYPE_NAMES = {
    TYPE_IDENTITY:    'IDENTITY',
    TYPE_OBSERVATION: 'OBSERVATION',
    TYPE_ENCRYPTED:   'ENCRYPTED',
    TYPE_CHAIN:       'CHAIN',
}


def _build_header(dot_type: int, flags: int = 0, tlv_count: int = 0) -> bytes:
    """Pack the 10-byte DOT header."""
    return (
        DOT_MAGIC +
        struct.pack('B', DOT_VERSION) +
        struct.pack('B', CRYPTO_SUITE_ED25519) +
        struct.pack('>H', flags) +
        struct.pack('B', dot_type) +
        struct.pack('B', tlv_count)
    )


def _build_body(payload: bytes, observer_pubkey: bytes, prev_hash: bytes,
                timestamp_us: int = None) -> bytes:
    """Pack the variable-length DOT body."""
    if timestamp_us is None:
        timestamp_us = int(time.time() * 1_000_000)
    if prev_hash is None:
        prev_hash = GENESIS_PREV_HASH
    assert len(observer_pubkey) == 32, "Observer key must be 32 bytes"
    assert len(prev_hash) == 32, "prev_hash must be 32 bytes"

    return (
        struct.pack('>Q', timestamp_us) +
        observer_pubkey +
        prev_hash +
        struct.pack('>I', len(payload)) +
        payload
    )


def create_dot(payload, signing_key, verify_key,
               dot_type: int = TYPE_OBSERVATION,
               prev_hash: bytes = None,
               flags: int = 0,
               tlvs: bytes = b'',
               timestamp_us: int = None) -> bytes:
    """Create a complete signed DOT.

    Args:
        payload: str or bytes
        signing_key: pynacl SigningKey
        verify_key: pynacl VerifyKey
        dot_type: one of TYPE_* constants
        prev_hash: 32-byte bytes or None (genesis = 32 zero bytes)
        flags: header flags
        tlvs: pre-encoded TLV extension bytes
        timestamp_us: microseconds since epoch (default: now)

    Returns: raw bytes of the complete DOT
    """
    if isinstance(payload, str):
        payload = payload.encode('utf-8')

    observer = pubkey_bytes(verify_key)
    tlv_count = 0  # no TLV extensions for minimal DOT (tlvs param reserved for future)

    header = _build_header(dot_type, flags=flags, tlv_count=tlv_count)
    body = _build_body(payload, observer, prev_hash, timestamp_us)

    # Signature covers: header + TLV extensions + body
    signable = header + tlvs + body
    sig = sign(signable, signing_key)
    assert len(sig) == 64, f"Signature must be 64 bytes, got {len(sig)}"

    return signable + sig


def parse_dot(raw: bytes) -> dict:
    """Parse a raw DOT into a dictionary of all fields.

    Returns dict with keys:
      magic, version, crypto_suite, flags, dot_type, tlv_count,
      tlvs, timestamp_us, observer, prev_hash, payload_len, payload, signature,
      signable (bytes before signature), raw (full bytes)
    """
    if len(raw) < 10:
        raise ValueError(f"DOT too short: {len(raw)} bytes")

    offset = 0

    # --- HEADER ---
    magic = raw[offset:offset+4]
    offset += 4
    if magic != DOT_MAGIC:
        raise ValueError(f"Invalid magic: {magic!r}")

    version = raw[offset]; offset += 1
    crypto_suite = raw[offset]; offset += 1
    flags = struct.unpack('>H', raw[offset:offset+2])[0]; offset += 2
    dot_type = raw[offset]; offset += 1
    tlv_count = raw[offset]; offset += 1

    # --- TLV EXTENSIONS ---
    tlvs = []
    for _ in range(tlv_count):
        tag = struct.unpack('>H', raw[offset:offset+2])[0]; offset += 2
        length = struct.unpack('>H', raw[offset:offset+2])[0]; offset += 2
        value = raw[offset:offset+length]; offset += length
        tlvs.append({'tag': tag, 'length': length, 'value': value})

    # --- BODY ---
    timestamp_us = struct.unpack('>Q', raw[offset:offset+8])[0]; offset += 8
    observer = raw[offset:offset+32]; offset += 32
    prev_hash = raw[offset:offset+32]; offset += 32
    payload_len = struct.unpack('>I', raw[offset:offset+4])[0]; offset += 4
    payload = raw[offset:offset+payload_len]; offset += payload_len

    # --- SIGNATURE ---
    if len(raw) - offset < 64:
        raise ValueError(f"DOT truncated: missing signature. Got {len(raw)-offset} bytes, need 64")
    signature = raw[offset:offset+64]
    signable = raw[:offset]  # everything before the signature

    return {
        'magic': magic,
        'version': version,
        'crypto_suite': crypto_suite,
        'flags': flags,
        'dot_type': dot_type,
        'dot_type_name': TYPE_NAMES.get(dot_type, f'UNKNOWN(0x{dot_type:02x})'),
        'tlv_count': tlv_count,
        'tlvs': tlvs,
        'timestamp_us': timestamp_us,
        'observer': observer,
        'prev_hash': prev_hash,
        'payload_len': payload_len,
        'payload': payload,
        'signature': signature,
        'signable': signable,
        'raw': raw,
        'total_size': len(raw),
    }


def verify_dot(raw: bytes) -> bool:
    """Verify the Ed25519 signature of a raw DOT.
    Returns True if valid, False otherwise.
    """
    try:
        parsed = parse_dot(raw)
    except (ValueError, struct.error):
        return False

    from dot_crypto import verify_key_from_bytes
    verify_key = verify_key_from_bytes(parsed['observer'])
    return verify(parsed['signable'], parsed['signature'], verify_key)
