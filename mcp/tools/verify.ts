import * as ed from '@noble/ed25519';

function hexToBytes(h: string): Uint8Array {
  const r = new Uint8Array(h.length / 2);
  for (let i = 0; i < h.length; i += 2) r[i / 2] = parseInt(h.slice(i, i + 2), 16);
  return r;
}
function concatBytes(...arrays: Uint8Array[]): Uint8Array {
  const total = arrays.reduce((s, a) => s + a.length, 0);
  const r = new Uint8Array(total); let off = 0;
  for (const a of arrays) { r.set(a, off); off += a.length; }
  return r;
}

export const verifyTool = {
  name: 'axxis.verify',
  description:
    'Verify the cryptographic signature of a DOT observation. Returns validity, observer identity, and decoded fields.',
  inputSchema: {
    type: 'object',
    properties: {
      dot: {
        type: 'object',
        description:
          'The DOT object with timestamp, observer, prevHash, payload, signature, hash fields.',
      },
    },
    required: ['dot'],
  },
};

export async function handleVerify(args: Record<string, unknown>) {
  const dot = args.dot as {
    timestamp: number;
    observer: string;
    prevHash: string;
    payload: string;
    signature: string;
    hash: string;
  };

  try {
    const payloadBytes = new TextEncoder().encode(dot.payload);
    const timestampBytes = new Uint8Array(8);
    new DataView(timestampBytes.buffer).setBigUint64(0, BigInt(dot.timestamp * 1000), false);

    const prevHashBytes = hexToBytes(dot.prevHash);
    const observerBytes = hexToBytes(dot.observer);
    const payloadLenBytes = new Uint8Array(4);
    new DataView(payloadLenBytes.buffer).setUint32(0, payloadBytes.length, false);

    const message = concatBytes(
      timestampBytes,
      observerBytes,
      prevHashBytes,
      payloadLenBytes,
      payloadBytes
    );

    const valid = await ed.verifyAsync(
      hexToBytes(dot.signature),
      message,
      observerBytes
    );

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              valid,
              observer: dot.observer.slice(0, 16) + '...',
              payload: dot.payload,
              timestamp: new Date(dot.timestamp).toISOString(),
              prevHash: dot.prevHash.slice(0, 16) + '...',
              hash: dot.hash.slice(0, 16) + '...',
              isGenesis: dot.prevHash === '0'.repeat(64),
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (e: unknown) {
    return {
      content: [
        { type: 'text', text: JSON.stringify({ valid: false, error: String(e) }) },
      ],
    };
  }
}
