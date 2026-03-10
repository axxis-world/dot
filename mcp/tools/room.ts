export const roomTool = {
  name: 'axxis.room',
  description:
    'Read the current observation chain from axxis.world/room. Returns all observations with verification status.',
  inputSchema: {
    type: 'object',
    properties: {
      limit: {
        type: 'number',
        description: 'Max observations to return (default 20, max 100).',
      },
      reverse: {
        type: 'boolean',
        description: 'Return newest first (default true).',
      },
    },
  },
};

interface ChainObservation {
  timestamp: number;
  observer: string;
  payload: string;
  hash: string;
  prevHash: string;
}

export async function handleRoom(args: Record<string, unknown>) {
  const limit = Math.min((args.limit as number) || 20, 100);
  const reverse = args.reverse !== false;

  try {
    const res = await fetch('https://axxis.world/api/chain');

    if (!res.ok) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              error: `axxis.world returned ${res.status}`,
              chainUrl: 'https://axxis.world/room',
            }),
          },
        ],
      };
    }

    const data = (await res.json()) as {
      chain: ChainObservation[];
      count: number;
    };

    let chain = data.chain;
    if (reverse) chain = [...chain].reverse();
    chain = chain.slice(0, limit);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              total: data.count,
              returned: chain.length,
              chainUrl: 'https://axxis.world/room',
              observations: chain.map(o => ({
                hash: o.hash.slice(0, 16) + '...',
                observer: o.observer.slice(0, 16) + '...',
                timestamp: new Date(o.timestamp).toISOString(),
                payload: o.payload,
                isGenesis: o.prevHash === '0'.repeat(64),
              })),
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
        {
          type: 'text',
          text: JSON.stringify({
            error: `Could not reach axxis.world: ${String(e)}`,
            chainUrl: 'https://axxis.world/room',
            note: 'The chain endpoint is not yet live. Tools are scaffolded and ready.',
          }),
        },
      ],
    };
  }
}
