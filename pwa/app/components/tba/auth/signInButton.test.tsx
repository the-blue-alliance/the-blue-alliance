import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { FirebaseError } from 'firebase/app';
import type { AuthProvider } from 'firebase/auth';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import SignInButton from '~/components/tba/auth/signInButton';

const mocks = vi.hoisted(() => ({
  auth: null as object | null,
  signInWithPopup:
    vi.fn<(auth: unknown, provider: unknown) => Promise<unknown>>(),
  signInWithRedirect:
    vi.fn<(auth: unknown, provider: unknown) => Promise<never>>(),
  logError: vi.fn<(data: unknown, message: string) => void>(),
}));

vi.mock('firebase/auth', () => ({
  signInWithPopup: mocks.signInWithPopup,
  signInWithRedirect: mocks.signInWithRedirect,
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
const AUTH = { name: 'auth' };

function renderButton() {
  render(
    <SignInButton
      provider={PROVIDER}
      logo="/logo.svg"
      text="Sign in with Test"
      className="bg-white"
    />,
  );
  return screen.getByRole('button', { name: /Sign in with Test/ });
}

describe('SignInButton', () => {
  beforeEach(() => {
    mocks.auth = AUTH;
  });

  test('renders the provider logo and label', () => {
    const button = renderButton();

    expect(button.className).toContain('bg-white');
    expect(
      screen.getByAltText('Sign in with Test logo').getAttribute('src'),
    ).toBe('/logo.svg');
  });

  test('does nothing without Firebase auth', () => {
    mocks.auth = null;

    fireEvent.click(renderButton());

    expect(mocks.signInWithPopup).not.toHaveBeenCalled();
  });

  test('signs in with a popup', async () => {
    mocks.signInWithPopup.mockResolvedValue({});

    fireEvent.click(renderButton());

    expect(mocks.signInWithPopup).toHaveBeenCalledWith(AUTH, PROVIDER);
    await Promise.resolve();
    expect(mocks.signInWithRedirect).not.toHaveBeenCalled();
    expect(mocks.logError).not.toHaveBeenCalled();
  });

  test.each([
    'auth/popup-blocked',
    'auth/cancelled-popup-request',
    'auth/operation-not-supported-in-this-environment',
  ])('falls back to a redirect on %s', async (code) => {
    mocks.signInWithPopup.mockRejectedValue(new FirebaseError(code, 'popup'));
    mocks.signInWithRedirect.mockReturnValue(new Promise(() => undefined));

    fireEvent.click(renderButton());

    await waitFor(() =>
      expect(mocks.signInWithRedirect).toHaveBeenCalledWith(AUTH, PROVIDER),
    );
    expect(mocks.logError).not.toHaveBeenCalled();
  });

  test('logs a failed redirect', async () => {
    const redirectError = new Error('redirect failed');
    mocks.signInWithPopup.mockRejectedValue(
      new FirebaseError('auth/popup-blocked', 'popup'),
    );
    mocks.signInWithRedirect.mockRejectedValue(redirectError);

    fireEvent.click(renderButton());

    await waitFor(() =>
      expect(mocks.logError).toHaveBeenCalledWith(
        { error: redirectError },
        'Error during redirect sign-in',
      ),
    );
  });

  test('logs other sign-in errors without redirecting', async () => {
    const error = new FirebaseError('auth/popup-closed-by-user', 'closed');
    mocks.signInWithPopup.mockRejectedValue(error);

    fireEvent.click(renderButton());

    await waitFor(() =>
      expect(mocks.logError).toHaveBeenCalledWith(
        { error },
        'Error during sign-in',
      ),
    );
    expect(mocks.signInWithRedirect).not.toHaveBeenCalled();
  });

  test('logs non-Firebase errors', async () => {
    const error = new Error('unexpected');
    mocks.signInWithPopup.mockRejectedValue(error);

    fireEvent.click(renderButton());

    await waitFor(() =>
      expect(mocks.logError).toHaveBeenCalledWith(
        { error },
        'Error during sign-in',
      ),
    );
  });
});
