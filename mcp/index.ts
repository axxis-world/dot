import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { sealTool, handleSeal } from './tools/seal.js';
import { verifyTool, handleVerify } from './tools/verify.js';
import { observeTool, handleObserve } from './tools/observe.js';
import { roomTool, handleRoom } from './tools/room.js';
import { searchTool, handleSearch } from './tools/search.js';

const server = new Server(
  { name: 'open-axxis', version: '0.1.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [sealTool, verifyTool, observeTool, roomTool, searchTool],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case 'axxis.seal':
      return handleSeal(args as Record<string, unknown>);
    case 'axxis.verify':
      return handleVerify(args as Record<string, unknown>);
    case 'axxis.observe':
      return handleObserve(args as Record<string, unknown>);
    case 'axxis.room':
      return handleRoom(args as Record<string, unknown>);
    case 'axxis.search':
      return handleSearch(args as Record<string, unknown>);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error('[open-axxis] MCP server running on stdio');
