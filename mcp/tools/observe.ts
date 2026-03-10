export const observeTool = {
  name: 'axxis.observe',
  description:
    'Submit a signed observation to the public DOT chain at axxis.world. Signs and seals a DOT, then posts it to the chain. Returns the chain hash.',
  inputSchema: {
    type: 'object',
    properties: {
      payload: {
        type: 'string',
        description: 'Your observation.',
      },
      secretKey: {
        type: 'string',
        description:
          'Your Ed25519 secret key (hex). Generates ephemeral if omitted.',
      },
    },
    required: ['payload'],
  },
};

export async function handleObserve(args: Record<string, unknown>) {
  // Get current chain tip
  let prevHash = '0'.repeat(64);
  try {
    const chainRes = await fetch('https://axxis.world/api/chain');
    if (chainRes.ok) {
      const chainData = (await chainRes.json()) as {
        chain: Array<{ hash: string }>;
      };
      if (chainData.chain && chainData.chain.length > 0) {
        prevHash = chainData.chain[chainData.chain.length - 1].hash;
      }
    }
  } catch {
    console.error('[observe] Could not fetch chain tip, using genesis hash');
  }

  // Seal the DOT
  const { handleSeal } = await import('./seal.js');
  const sealResult = await handleSeal({ ...args, prevHash });
  const sealData = JSON.parse(
    (sealResult.content[0] as { text: string }).text
  ) as { success: boolean; dot: Record<string, unknown> };

  if (!sealData.success) {
    return {
      content: [
        { type: 'text', text: JSON.stringify({ error: 'Seal failed' }) },
      ],
    };
  }

  // Attempt to submit to chain
  let submitData: Record<string, unknown> = {};
  let submitOk = false;
  try {
    const submitRes = await fetch('https://axxis.world/api/observe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sealData.dot),
    });
    submitOk = submitRes.ok;
    submitData = (await submitRes.json()) as Record<string, unknown>;
  } catch {
    submitData = { note: 'axxis.world/api not reachable — DOT sealed locally only' };
  }

  const dot = sealData.dot as {
    hash: string;
    observer: string;
    payload: string;
    timestamp: number;
    prevHash: string;
    signature: string;
  };

  // Broadcast to Nostr relays if chain submission succeeded
  let nostr: { relaysReached: number; eventId: string } | null = null;
  if (submitOk) {
    try {
      const { broadcastDOT } = await import('../nostr/broadcast.js');
      nostr = await broadcastDOT(dot);
    } catch {
      // Nostr broadcast is best-effort
    }
  }

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(
          {
            success: submitOk,
            hash: dot.hash,
            observer: dot.observer.slice(0, 16) + '...',
            payload: args.payload,
            chainUrl: 'https://axxis.world/room',
            nostr,
            ...submitData,
          },
          null,
          2
        ),
      },
    ],
  };
}
