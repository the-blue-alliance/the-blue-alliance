import { type NetworkFixture, defineNetworkFixture } from '@msw/playwright';
import { test as base } from '@playwright/test';
import { HttpResponse, http } from 'msw';

import {
  type SdkData,
  type SdkFn,
  type SdkOptions,
  type SsrMock,
  describeTbaRequest,
} from '~/test/tbaRequest';

type MockTba = <F extends SdkFn>(
  sdkFn: F,
  options: SdkOptions<F>,
  body: SdkData<F>,
) => Promise<void>;

export const test = base.extend<{ network: NetworkFixture; mockTba: MockTba }>({
  network: async ({ context }, use) => {
    const network = defineNetworkFixture({
      context,
      handlers: [],
      onUnhandledFrame: 'bypass',
    });
    await network.enable();
    await use(network);
    await network.disable();
  },
  mockTba: async ({ context, network }, use) => {
    const mockId = crypto.randomUUID();
    const controlUrl = `http://localhost:3001/${mockId}`;
    const ssrMocks: SsrMock[] = [];
    await context.addCookies([
      {
        name: 'e2e-test-id',
        value: mockId,
        domain: 'localhost',
        path: '/',
      },
    ]);
    await use(async (sdkFn, options, body) => {
      const { method, path } = describeTbaRequest(sdkFn, options);
      ssrMocks.push({ method: method.toUpperCase(), path, body });
      await fetch(controlUrl, {
        method: 'PUT',
        body: JSON.stringify(ssrMocks),
      });
      network.use(http[method](`*${path}`, () => HttpResponse.json(body)));
    });
    await fetch(controlUrl, { method: 'DELETE' });
  },
});

export { expect } from '@playwright/test';
