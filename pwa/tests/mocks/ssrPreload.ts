import { http, passthrough } from 'msw';
import { setupServer } from 'msw/node';
import { AsyncLocalStorage } from 'node:async_hooks';
import { subscribe } from 'node:diagnostics_channel';
import { type IncomingMessage, createServer } from 'node:http';
import { text } from 'node:stream/consumers';

import type { SsrMock } from '~/test/tbaRequest';

globalThis.__TBA_E2E_MOCKS__ = true;

const testIds = new AsyncLocalStorage<string | undefined>();
const mocksByTest = new Map<string, SsrMock[]>();

// Published synchronously right before the server emits 'request', so
// enterWith scopes the whole SSR render to this test without touching server.ts.
subscribe('http.server.request.start', (message) => {
  const { request } = message as { request: IncomingMessage };
  testIds.enterWith(
    /(?:^|; )e2e-test-id=([^;]+)/.exec(request.headers.cookie ?? '')?.[1],
  );
});

setupServer(
  http.all('*/api/v3/*', ({ request }) => {
    const { pathname } = new URL(request.url);
    const mock = mocksByTest
      .get(testIds.getStore() ?? '')
      ?.find(
        (m) => m.method === request.method && pathname === `/api/v3${m.path}`,
      );
    return mock ? Response.json(mock.body) : passthrough();
  }),
).listen({ onUnhandledFrame: 'bypass' });

createServer(async (req, res) => {
  const testId = new URL(req.url ?? '', 'http://localhost').pathname.slice(1);
  if (req.method === 'PUT') {
    mocksByTest.set(testId, JSON.parse(await text(req)));
  } else {
    mocksByTest.delete(testId);
  }
  res.writeHead(204).end();
}).listen(3001);
