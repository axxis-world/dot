import { embed, loadCache, saveCache, cosine } from '../lib/embed.js';

export const searchTool = {
  name: 'axxis.search',
  description:
    'Semantic search across the DOT chain. Find observations by meaning, not keywords. ' +
    'First call downloads the 25MB all-MiniLM-L6-v2 model (once, then cached).',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'What you are looking for — natural language, any topic.',
      },
      limit: {
        type: 'number',
        description: 'Max results to return (default 5, max 20).',
      },
    },
    required: ['query'],
  },
};

type RawDOT = {
  hash: string;
  payload: string;
  observer: string;
  timestamp: number;
  prevHash: string;
};

function parsePayload(payload: string): { text: string; name?: string } {
  try {
    const d = JSON.parse(payload);
    if (d && typeof d.t === 'string') return { text: d.t, name: d.n || undefined };
  } catch { /* plain text */ }
  return { text: payload };
}

export async function handleSearch(args: Record<string, unknown>) {
  const query = args.query as string;
  const limit = Math.min(Number(args.limit) || 5, 20);

  // Fetch full chain from axxis.world
  let chain: RawDOT[] = [];
  try {
    const res = await fetch('https://axxis.world/api/chain');
    const data = await res.json() as { chain: RawDOT[] };
    chain = data.chain || [];
  } catch {
    return { content: [{ type: 'text', text: JSON.stringify({ error: 'Could not reach axxis.world/api/chain' }) }] };
  }

  if (chain.length === 0) {
    return { content: [{ type: 'text', text: JSON.stringify({ query, results: [], message: 'Chain is empty' }) }] };
  }

  console.error(`[search] embedding ${chain.length} DOTs + query...`);

  // Load local cache, embed any uncached DOTs
  const cache = loadCache();
  let updated = false;

  for (const dot of chain) {
    if (!cache[dot.hash]) {
      const { text } = parsePayload(dot.payload);
      cache[dot.hash] = await embed(text);
      updated = true;
    }
  }

  if (updated) saveCache(cache);

  // Embed query and rank
  const queryVec = await embed(query);

  const results = chain
    .map(dot => {
      const { text, name } = parsePayload(dot.payload);
      return {
        hash: dot.hash.slice(0, 16) + '...',
        observer: name || dot.observer.slice(0, 8) + '...',
        text,
        timestamp: new Date(dot.timestamp).toISOString(),
        score: parseFloat(cosine(queryVec, cache[dot.hash]).toFixed(4)),
      };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);

  return {
    content: [{
      type: 'text',
      text: JSON.stringify({ query, total_searched: chain.length, results }, null, 2),
    }],
  };
}
