import { act, waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import {
  addWebhook,
  deleteWebhook,
  listWebhooks,
  pingMobileClient,
  sendWebhookTest,
  sendWebhookVerification,
  verifyWebhook,
} from '~/api/tba/mobile/sdk.gen';
import type { Webhook } from '~/api/tba/mobile/types.gen';
import { useWebhooks } from '~/lib/hooks/useWebhooks';
import { mockTbaApi, mockTbaApiWith } from '~/test/msw';
import { renderHookWithClient } from '~/test/render';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn<() => { user: unknown }>(),
}));

vi.mock('~/components/tba/auth/auth', () => ({ useAuth: mocks.useAuth }));

const USER = { uid: 'user-1', getIdToken: () => Promise.resolve('token-1') };

const HOOK_A: Webhook = {
  webhook_id: '1',
  name: 'Scouting',
  url: 'https://a.example.com',
  secret: 'secret-a',
  verified: false,
};
const HOOK_B: Webhook = {
  webhook_id: '2',
  name: 'Stats',
  url: 'https://b.example.com',
  secret: 'secret-b',
  verified: true,
};

async function renderLoaded() {
  const hook = renderHookWithClient(() => useWebhooks());
  await waitFor(() => expect(hook.result.current.isLoading).toBe(false));
  return hook;
}

describe('useWebhooks', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
    mockTbaApi(listWebhooks, {}, { code: 200, webhooks: [HOOK_A] });
  });

  test('does not load webhooks when signed out', async () => {
    mocks.useAuth.mockReturnValue({ user: null });

    const { result } = await renderLoaded();

    expect(result.current.webhooks).toEqual([]);
  });

  test('loads the webhooks', async () => {
    const { result } = await renderLoaded();

    expect(result.current.webhooks).toEqual([HOOK_A]);
  });

  test('returns no webhooks when loading fails', async () => {
    mockTbaApiWith(
      listWebhooks,
      {},
      () => new HttpResponse(null, { status: 500 }),
    );

    const { result } = await renderLoaded();

    expect(result.current.webhooks).toEqual([]);
  });

  test('sends the name and URL when adding', async () => {
    const requests = mockTbaApi(addWebhook, {}, { code: 200, webhook: HOOK_B });
    const { result } = await renderLoaded();

    await act(() =>
      result.current.addWebhook({ name: 'Stats', url: HOOK_B.url }),
    );

    expect(await requests[0].json()).toEqual({
      name: 'Stats',
      url: HOOK_B.url,
    });
  });

  test('authenticates an add with the user token', async () => {
    const requests = mockTbaApi(addWebhook, {}, { code: 200, webhook: HOOK_B });
    const { result } = await renderLoaded();

    await act(() =>
      result.current.addWebhook({ name: 'Stats', url: HOOK_B.url }),
    );

    expect(requests[0].headers.get('Authorization')).toBe('Bearer token-1');
  });

  test('lists an added webhook', async () => {
    mockTbaApi(addWebhook, {}, { code: 200, webhook: HOOK_B });
    const { result } = await renderLoaded();

    await act(() =>
      result.current.addWebhook({ name: 'Stats', url: HOOK_B.url }),
    );

    await waitFor(() =>
      expect(result.current.webhooks).toEqual([HOOK_A, HOOK_B]),
    );
  });

  test('replaces a webhook that was added again', async () => {
    const readded = { ...HOOK_A, secret: 'new-secret' };
    mockTbaApi(addWebhook, {}, { code: 200, webhook: readded });
    const { result } = await renderLoaded();

    await act(() =>
      result.current.addWebhook({ name: 'Scouting', url: HOOK_A.url }),
    );

    await waitFor(() => expect(result.current.webhooks).toEqual([readded]));
  });

  test('rejects an add with the server message', async () => {
    mockTbaApi(
      addWebhook,
      {},
      { code: 400, message: 'A name and URL are required' },
    );
    const { result } = await renderLoaded();

    await expect(
      result.current.addWebhook({ name: '', url: '' }),
    ).rejects.toThrow('A name and URL are required');
  });

  test('marks a verified webhook as verified', async () => {
    mockTbaApi(verifyWebhook, {}, { code: 200 });
    const { result } = await renderLoaded();

    await act(() =>
      result.current.verifyWebhook({ webhook_id: '1', code: 'abc' }),
    );

    await waitFor(() => expect(result.current.webhooks[0].verified).toBe(true));
  });

  test('rejects a wrong verification code', async () => {
    mockTbaApi(
      verifyWebhook,
      {},
      { code: 400, message: 'Incorrect verification code' },
    );
    const { result } = await renderLoaded();

    await expect(
      result.current.verifyWebhook({ webhook_id: '1', code: 'nope' }),
    ).rejects.toThrow('Incorrect verification code');
  });

  test('marks a webhook unverified after sending a new code', async () => {
    mockTbaApi(listWebhooks, {}, { code: 200, webhooks: [HOOK_B] });
    mockTbaApi(sendWebhookVerification, {}, { code: 200 });
    const { result } = await renderLoaded();

    await act(() => result.current.resendVerification('2'));

    await waitFor(() =>
      expect(result.current.webhooks[0].verified).toBe(false),
    );
  });

  test('removes a deleted webhook', async () => {
    mockTbaApi(deleteWebhook, {}, { code: 200 });
    const { result } = await renderLoaded();

    await act(() => result.current.deleteWebhook('1'));

    await waitFor(() => expect(result.current.webhooks).toEqual([]));
  });

  test('keeps a webhook whose delete failed', async () => {
    mockTbaApi(deleteWebhook, {}, { code: 404 });
    const { result } = await renderLoaded();

    await expect(result.current.deleteWebhook('1')).rejects.toThrow(
      'Failed to delete webhook',
    );
    expect(result.current.webhooks).toEqual([HOOK_A]);
  });

  test('pings a webhook by its URL', async () => {
    const requests = mockTbaApi(pingMobileClient, {}, { code: 200 });
    const { result } = await renderLoaded();

    await act(() => result.current.pingWebhook(HOOK_A.url));

    expect(await requests[0].json()).toEqual({ mobile_id: HOOK_A.url });
  });

  test('rejects a failed ping', async () => {
    mockTbaApi(pingMobileClient, {}, { code: 500 });
    const { result } = await renderLoaded();

    await expect(result.current.pingWebhook(HOOK_A.url)).rejects.toThrow(
      'Failed to send ping',
    );
  });

  test('rejects a failed test notification with the server message', async () => {
    mockTbaApi(
      sendWebhookTest,
      {},
      { code: 400, message: 'Webhook is not verified' },
    );
    const { result } = await renderLoaded();

    await expect(
      result.current.sendTest({
        webhook_id: '1',
        notification_type: 'match_score',
      }),
    ).rejects.toThrow('Webhook is not verified');
  });
});
