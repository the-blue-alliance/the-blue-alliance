import { describe, expect, it, vi } from 'vitest';

import { createTokenRefresher, shouldRefreshToken } from '~/lib/authRefresh';

describe('shouldRefreshToken', () => {
  it('refreshes when the tab is visible and a user is signed in', () => {
    expect(shouldRefreshToken('visible', true)).toBe(true);
  });

  it('does not refresh when no user is signed in', () => {
    expect(shouldRefreshToken('visible', false)).toBe(false);
  });

  it('does not refresh while the tab is hidden', () => {
    expect(shouldRefreshToken('hidden', true)).toBe(false);
  });
});

describe('createTokenRefresher', () => {
  it('uses one request while a token refresh is pending', () => {
    const getIdToken = vi.fn<() => Promise<string>>(
      () => new Promise<string>(() => undefined),
    );
    const refreshToken = createTokenRefresher(() => ({ getIdToken }));

    void refreshToken();
    void refreshToken();

    expect(getIdToken).toHaveBeenCalledOnce();
  });

  it('lets Firebase decide whether the token needs refreshing', () => {
    const getIdToken = vi.fn<() => Promise<string>>(() =>
      Promise.resolve('token'),
    );
    const refreshToken = createTokenRefresher(() => ({ getIdToken }));

    void refreshToken();

    expect(getIdToken).toHaveBeenCalledWith();
  });

  it('allows another request after the pending refresh finishes', async () => {
    const getIdToken = vi.fn<() => Promise<string>>(() =>
      Promise.resolve('token'),
    );
    const refreshToken = createTokenRefresher(() => ({ getIdToken }));

    await refreshToken();
    void refreshToken();

    expect(getIdToken).toHaveBeenCalledTimes(2);
  });
});
