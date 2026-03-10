import * as ed from '@noble/ed25519';

function bytesToHex(b: Uint8Array): string {
  return Array.from(b).map(x => x.toString(16).padStart(2, '0')).join('');
}
function hexToBytes(h: string): Uint8Array {
  const r = new Uint8Array(h.length / 2);
  for (let i = 0; i < h.length; i += 2) r[i / 2] = parseInt(h.slice(i, i + 2), 16);
  return r;
}
function concatBytes(...arrays: Uint8Array[]): Uint8Array {
  const total = arrays.reduce((s, a) => s + a.length, 0);
  const r = new Uint8Array(total);
  let off = 0;
  for (const a of arrays) { r.set(a, off); off += a.length; }
  return r;
}

export const sealTool = {
  name: 'axxis.seal',
  description:
    'Create and cryptographically sign a DOT observation. Returns the signed DOT and its SHA-256 hash. The observer keypair is generated ephemerally or provided.',
  inputSchema: {
    type: 'object',
    properties: {
      payload: {
        type: 'string',
        description: 'The observation to seal. What you witnessed, decided, or understood.',
      },
      secretKey: {
        type: 'string',
        description:
          'Hex-encoded Ed25519 secret key (32 bytes). If omitted, generates an ephemeral keypair.',
      },
      prevHash: {
        type: 'string',
        description:
          'SHA-256 hash of the previous DOT (hex). Omit for genesis observation.',
      },
    },
    required: ['payload'],
  },
};

export async function handleSeal(args: Record<string, unknown>) {
  const payload = args.payload as string;
  const prevHash = (args.prevHash as string) || '0'.repeat(64);

  let secretKeyBytes: Uint8Array;
  let isEphemeral = false;

  if (args.secretKey) {
    secretKeyBytes = hexToBytes(args.secretKey as string);
  } else {
    secretKeyBytes = ed.utils.randomSecretKey();
    isEphemeral = true;
  }

  const pubKeyBytes = await ed.getPublicKeyAsync(secretKeyBytes);
  const pubKeyHex = bytesToHex(pubKeyBytes);

  const timestamp = Date.now();
  const payloadBytes = new TextEncoder().encode(payload);

  const timestampBytes = new Uint8Array(8);
  new DataView(timestampBytes.buffer).setBigUint64(0, BigInt(timestamp * 1000), false);

  const prevHashBytes = hexToBytes(prevHash);

  const payloadLenBytes = new Uint8Array(4);
  new DataView(payloadLenBytes.buffer).setUint32(0, payloadBytes.length, false);

  const message = concatBytes(
    timestampBytes,
    pubKeyBytes,
    prevHashBytes,
    payloadLenBytes,
    payloadBytes
  );

  const signature = await ed.signAsync(message, secretKeyBytes);

  const dotBytes = concatBytes(message, signature);
  // Use SubtleCrypto for hash — cast to ArrayBuffer to satisfy TypeScript
  const hashBuf = await crypto.subtle.digest('SHA-256', dotBytes.buffer.slice(dotBytes.byteOffset, dotBytes.byteOffset + dotBytes.byteLength) as ArrayBuffer);
  const hash = bytesToHex(new Uint8Array(hashBuf));

  const dot = {
    timestamp,
    observer: pubKeyHex,
    prevHash,
    payload,
    signature: bytesToHex(signature),
    hash,
  };

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(
          {
            success: true,
            dot,
            secretKey: isEphemeral ? bytesToHex(secretKeyBytes) : undefined,
            note: isEphemeral
              ? 'Ephemeral keypair generated. Save secretKey to sign future linked observations.'
              : 'Signed with provided key.',
          },
          null,
          2
        ),
      },
    ],
  };
}
