import {
  act,
  render,
  renderHook,
  screen,
  waitFor,
} from '@testing-library/react';
import type { AuthProvider } from 'firebase/auth';
import type { PropsWithChildren } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { AuthContextProvider, useAuth } from '~/components/tba/auth/auth';

interface FakeUser {
  uid: string;
  getIdToken: () => Promise<string>;
}

const mocks = vi.hoisted(() => ({
  auth: null as { currentUser: FakeUser | null } | null,
  onIdTokenChanged:
    vi.fn<(auth: unknown, listener: (user: unknown) => void) => () => void>(),
  unsubscribe: vi.fn<() => void>(),
  getRedirectResult: vi.fn<(auth: unknown) => Promise<unknown>>(),
  signInWithPopup:
    vi.fn<(auth: unknown, provider: unknown) => Promise<{ user: unknown }>>(),
  signOut: vi.fn<(auth: unknown) => Promise<void>>(),
  logError: vi.fn<(data: unknown, message: string) => void>(),
}));

vi.mock('firebase/auth', () => ({
  getRedirectResult: mocks.getRedirectResult,
  onIdTokenChanged: mocks.onIdTokenChanged,
  signInWithPopup: mocks.signInWithPopup,
  signOut: mocks.signOut,
}));

vi.mock('~/firebase/firebaseConfig', () => ({
  get auth() {
    return mocks.auth;
  },
}));

vi.mock('~/lib/logger', () => ({
  createLogger: () => ({ error: mocks.logError }),
}));

const PROVIDER = { providerId: 'google.com' } as AuthProvider;

function makeUser(uid: string): FakeUser {
  return { uid, getIdToken: vi.fn<() => Promise<string>>() };
}

function wrapper({ children }: PropsWithChildren) {
  return <AuthContextProvider>{children}</AuthContextProvider>;
}

function renderAuth() {
  return renderHook(() => useAuth(), { wrapper });
}

function emitUser(user: FakeUser | null) {
  const listener = mocks.onIdTokenChanged.mock.calls[0][1];
  act(() => listener(user));
}

function setVisibility(state: DocumentVisibilityState) {
  Object.defineProperty(document, 'visibilityState', {
    configurable: true,
    get: () => state,
  });
}

describe('useAuth', () => {
  test('requires an AuthContextProvider', () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);

    expect(() => renderHook(() => useAuth())).toThrow(
      'useAuth must be used within an AuthProvider',
    );
  });
});

describe('AuthContextProvider without Firebase auth (SSR)', () => {
  beforeEach(() => {
    mocks.auth = null;
  });

  test('stays loading and makes login and logout no-ops', async () => {
    const { result } = renderAuth();

    expect(result.current.user).toBeNull();
    expect(result.current.isInitialLoading).toBe(true);
    await act(() => result.current.login(PROVIDER));
    await act(() => result.current.logout());

    expect(mocks.onIdTokenChanged).not.toHaveBeenCalled();
    expect(mocks.signInWithPopup).not.toHaveBeenCalled();
    expect(mocks.signOut).not.toHaveBeenCalled();
  });
});

describe('AuthContextProvider', () => {
  beforeEach(() => {
    mocks.auth = { currentUser: null };
    mocks.onIdTokenChanged.mockReturnValue(mocks.unsubscribe);
    mocks.getRedirectResult.mockResolvedValue(null);
    setVisibility('visible');
  });

  test('renders its children', () => {
    render(
      <AuthContextProvider>
        <p>Child content</p>
      </AuthContextProvider>,
    );

    expect(screen.getByText('Child content')).toBeTruthy();
  });

  test('starts from the cached user and follows ID token changes', () => {
    const cached = makeUser('cached');
    mocks.auth = { currentUser: cached };
    const { result } = renderAuth();

    expect(result.current.user).toBe(cached);
    expect(result.current.isInitialLoading).toBe(true);
    expect(mocks.onIdTokenChanged).toHaveBeenCalledWith(
      mocks.auth,
      expect.any(Function),
    );

    const next = makeUser('next');
    emitUser(next);
    expect(result.current.user).toBe(next);
    expect(result.current.isInitialLoading).toBe(false);

    emitUser(null);
    expect(result.current.user).toBeNull();
  });

  test('logs a failed sign-in redirect', async () => {
    const error = new Error('redirect failed');
    mocks.getRedirectResult.mockRejectedValue(error);

    renderAuth();

    await waitFor(() =>
      expect(mocks.logError).toHaveBeenCalledWith(
        { error },
        'Error resolving sign-in redirect',
      ),
    );
  });

  test('signs in with a popup', async () => {
    const user = makeUser('popup');
    mocks.signInWithPopup.mockResolvedValue({ user });
    const { result } = renderAuth();

    await act(() => result.current.login(PROVIDER));

    expect(mocks.signInWithPopup).toHaveBeenCalledWith(mocks.auth, PROVIDER);
    expect(result.current.user).toBe(user);
    expect(result.current.isInitialLoading).toBe(false);
  });

  test('signs out', async () => {
    mocks.signOut.mockResolvedValue();
    mocks.auth = { currentUser: makeUser('cached') };
    const { result } = renderAuth();

    await act(() => result.current.logout());

    expect(mocks.signOut).toHaveBeenCalledWith(mocks.auth);
    expect(result.current.user).toBeNull();
    expect(result.current.isInitialLoading).toBe(false);
  });

  test('refreshes the token when the tab becomes visible or focused', async () => {
    const user = makeUser('signed-in');
    vi.mocked(user.getIdToken).mockResolvedValue('token');
    mocks.auth = { currentUser: user };
    renderAuth();

    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });
    await waitFor(() => expect(user.getIdToken).toHaveBeenCalledTimes(1));

    act(() => {
      window.dispatchEvent(new Event('focus'));
    });
    await waitFor(() => expect(user.getIdToken).toHaveBeenCalledTimes(2));
  });

  test('skips refreshing while hidden or signed out', () => {
    const user = makeUser('signed-in');
    mocks.auth = { currentUser: user };
    renderAuth();

    setVisibility('hidden');
    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });
    setVisibility('visible');
    mocks.auth.currentUser = null;
    act(() => {
      window.dispatchEvent(new Event('focus'));
    });

    expect(user.getIdToken).not.toHaveBeenCalled();
  });

  test('logs a failed token refresh', async () => {
    const user = makeUser('signed-in');
    const error = new Error('network');
    vi.mocked(user.getIdToken).mockRejectedValue(error);
    mocks.auth = { currentUser: user };
    renderAuth();

    act(() => {
      window.dispatchEvent(new Event('focus'));
    });

    await waitFor(() =>
      expect(mocks.logError).toHaveBeenCalledWith(
        { error },
        'Error refreshing ID token',
      ),
    );
  });

  test('cleans up its listeners on unmount', () => {
    const user = makeUser('signed-in');
    mocks.auth = { currentUser: user };
    const { unmount } = renderAuth();

    unmount();
    window.dispatchEvent(new Event('focus'));

    expect(mocks.unsubscribe).toHaveBeenCalledTimes(1);
    expect(user.getIdToken).not.toHaveBeenCalled();
  });
});
