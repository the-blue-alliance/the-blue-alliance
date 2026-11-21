import { render } from '@testing-library/react';
import { OAuthProvider } from 'firebase/auth';
import { describe, expect, test, vi } from 'vitest';

import SignInWithAppleButton from '~/components/tba/auth/signInWithAppleButton';

const { signInButton } = vi.hoisted(() => ({
  signInButton: vi.fn<(props: Record<string, unknown>) => null>(() => null),
}));

vi.mock('~/components/tba/auth/signInButton', () => ({
  default: signInButton,
}));

describe('SignInWithAppleButton', () => {
  test('signs in with an Apple provider', () => {
    signInButton.mockReturnValue(null);

    render(<SignInWithAppleButton />);

    const props = signInButton.mock.calls[0][0];
    expect(props.provider).toBeInstanceOf(OAuthProvider);
    expect((props.provider as OAuthProvider).providerId).toBe('apple.com');
    expect(props.text).toBe('Sign in with Apple');
    expect(props.logo).toEqual(expect.any(String));
  });
});
