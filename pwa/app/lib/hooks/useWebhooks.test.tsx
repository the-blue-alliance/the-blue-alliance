import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { PropsWithChildren } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { Webhook } from '~/api/tba/mobile/types.gen';
import { useWebhooks } from '~/lib/hooks/useWebhooks';

type SdkFn = (options: unknown) => Promise<{ data?: unknown }>;

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn<() => { user: unknown }>(),
  listWebhooks: vi.fn<SdkFn>(),
  addWebhook: vi.fn<SdkFn>(),
  verifyWebhook: vi.fn<SdkFn>(),
  sendWebhookVerification: vi.fn<SdkFn>(),
  deleteWebhook: vi.fn<SdkFn>(),
  pingMobileClient: vi.fn<SdkFn>(),
  sendWebhookTest: vi.fn<SdkFn>(),
}));

vi.mock('~/components/tba/auth/auth', () => ({ useAuth: mocks.useAuth }));

vi.mock('~/api/tba/mobile/sdk.gen', () => ({
  listWebhooks: mocks.listWebhooks,
  addWebhook: mocks.addWebhook,
  verifyWebhook: mocks.verifyWebhook,
  sendWebhookVerification: mocks.sendWebhookVerification,
  deleteWebhook: mocks.deleteWebhook,
  pingMobileClient: mocks.pingMobileClient,
  sendWebhookTest: mocks.sendWebhookTest,
}));

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
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  }
  const hook = renderHook(() => useWebhooks(), { wrapper: Wrapper });
  await waitFor(() => expect(hook.result.current.isLoading).toBe(false));
  return hook;
}

describe('useWebhooks', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
    mocks.listWebhooks.mockResolvedValue({
      data: { code: 200, webhooks: [HOOK_A] },
    });
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
    mocks.listWebhooks.mockResolvedValue({ data: undefined });

    const { result } = await renderLoaded();

    expect(result.current.webhooks).toEqual([]);
  });

  test('sends the name and URL when adding', async () => {
    mocks.addWebhook.mockResolvedValue({
      data: { code: 200, webhook: HOOK_B },
    });
    const { result } = await renderLoaded();

    await act(() =>
      result.current.addWebhook({ name: 'Stats', url: HOOK_B.url }),
    );

    expect(mocks.addWebhook).toHaveBeenCalledWith({
      auth: 'token-1',
      body: { name: 'Stats', url: HOOK_B.url },
    });
  });

  test('lists an added webhook', async () => {
    mocks.addWebhook.mockResolvedValue({
      data: { code: 200, webhook: HOOK_B },
    });
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
    mocks.addWebhook.mockResolvedValue({
      data: { code: 200, webhook: readded },
    });
    const { result } = await renderLoaded();

    await act(() =>
      result.current.addWebhook({ name: 'Scouting', url: HOOK_A.url }),
    );

    await waitFor(() => expect(result.current.webhooks).toEqual([readded]));
  });

  test('rejects an add with the server message', async () => {
    mocks.addWebhook.mockResolvedValue({
      data: { code: 400, message: 'A name and URL are required' },
    });
    const { result } = await renderLoaded();

    await expect(
      result.current.addWebhook({ name: '', url: '' }),
    ).rejects.toThrow('A name and URL are required');
  });

  test('marks a verified webhook as verified', async () => {
    mocks.verifyWebhook.mockResolvedValue({ data: { code: 200 } });
    const { result } = await renderLoaded();

    await act(() =>
      result.current.verifyWebhook({ webhook_id: '1', code: 'abc' }),
    );

    await waitFor(() => expect(result.current.webhooks[0].verified).toBe(true));
  });

  test('rejects a wrong verification code', async () => {
    mocks.verifyWebhook.mockResolvedValue({
      data: { code: 400, message: 'Incorrect verification code' },
    });
    const { result } = await renderLoaded();

    await expect(
      result.current.verifyWebhook({ webhook_id: '1', code: 'nope' }),
    ).rejects.toThrow('Incorrect verification code');
  });

  test('marks a webhook unverified after sending a new code', async () => {
    mocks.listWebhooks.mockResolvedValue({
      data: { code: 200, webhooks: [HOOK_B] },
    });
    mocks.sendWebhookVerification.mockResolvedValue({ data: { code: 200 } });
    const { result } = await renderLoaded();

    await act(() => result.current.resendVerification('2'));

    await waitFor(() =>
      expect(result.current.webhooks[0].verified).toBe(false),
    );
  });

  test('removes a deleted webhook', async () => {
    mocks.deleteWebhook.mockResolvedValue({ data: { code: 200 } });
    const { result } = await renderLoaded();

    await act(() => result.current.deleteWebhook('1'));

    await waitFor(() => expect(result.current.webhooks).toEqual([]));
  });

  test('keeps a webhook whose delete failed', async () => {
    mocks.deleteWebhook.mockResolvedValue({ data: { code: 404 } });
    const { result } = await renderLoaded();

    await expect(result.current.deleteWebhook('1')).rejects.toThrow(
      'Failed to delete webhook',
    );
    expect(result.current.webhooks).toEqual([HOOK_A]);
  });

  test('pings a webhook by its URL', async () => {
    mocks.pingMobileClient.mockResolvedValue({ data: { code: 200 } });
    const { result } = await renderLoaded();

    await act(() => result.current.pingWebhook(HOOK_A.url));

    expect(mocks.pingMobileClient).toHaveBeenCalledWith({
      auth: 'token-1',
      body: { mobile_id: HOOK_A.url },
    });
  });

  test('rejects a failed ping', async () => {
    mocks.pingMobileClient.mockResolvedValue({ data: { code: 500 } });
    const { result } = await renderLoaded();

    await expect(result.current.pingWebhook(HOOK_A.url)).rejects.toThrow(
      'Failed to send ping',
    );
  });

  test('rejects a failed test notification with the server message', async () => {
    mocks.sendWebhookTest.mockResolvedValue({
      data: { code: 400, message: 'Webhook is not verified' },
    });
    const { result } = await renderLoaded();

    await expect(
      result.current.sendTest({
        webhook_id: '1',
        notification_type: 'match_score',
      }),
    ).rejects.toThrow('Webhook is not verified');
  });
});
