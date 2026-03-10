import { finalizeEvent, getPublicKey, generateSecretKey } from 'nostr-tools/pure';
import { Relay } from 'nostr-tools/relay';

const RELAYS = [
  'wss://relay.damus.io',
  'wss://nos.lol',
  'wss://relay.nostr.band',
  'wss://nostr.wine',
];

// Anonymous relay key for MCP-originated broadcasts
// Generated once per process — no persistent identity needed
let _relayKey: Uint8Array | null = null;
function getRelayKey(): Uint8Array {
  if (!_relayKey) _relayKey = generateSecretKey();
  return _relayKey;
}

export async function broadcastDOT(dot: {
  hash: string;
  observer: string;
  payload: string;
  timestamp: number;
  prevHash: string;
  signature: string;
}): Promise<{ relaysReached: number; eventId: string }> {
  const sk = getRelayKey();
  const pk = getPublicKey(sk);

  // NIP-1 kind:1 note with DOT metadata as tags
  const event = finalizeEvent(
    {
      kind: 1,
      created_at: Math.floor(dot.timestamp / 1000),
      tags: [
        ['t', 'dot-protocol'],
        ['t', 'axxis'],
        ['t', 'council-of-minds'],
        ['dot_hash', dot.hash],
        ['dot_observer', dot.observer.slice(0, 16)],
        ['dot_prev', dot.prevHash.slice(0, 16)],
      ],
      content: `${dot.payload}\n\n🔗 ${dot.hash.slice(0, 16)}... | axxis.world/room`,
    },
    sk
  );

  let relaysReached = 0;

  await Promise.allSettled(
    RELAYS.map(async (url) => {
      try {
        const relay = await Relay.connect(url);
        await relay.publish(event);
        relay.close();
        relaysReached++;
      } catch {
        // Relay unavailable — silently skip
      }
    })
  );

  return { relaysReached, eventId: event.id };
}
