import { vi } from 'vitest';

export const FAKE_USER = {
  uid: 'user-1',
  email: 'volunteer@example.com',
  getIdToken: () => Promise.resolve('token-1'),
};

export const useAuth =
  vi.fn<() => { isInitialLoading: boolean; user: typeof FAKE_USER | null }>();

export function signIn() {
  useAuth.mockReturnValue({ isInitialLoading: false, user: FAKE_USER });
}

export function signOut() {
  useAuth.mockReturnValue({ isInitialLoading: false, user: null });
}
