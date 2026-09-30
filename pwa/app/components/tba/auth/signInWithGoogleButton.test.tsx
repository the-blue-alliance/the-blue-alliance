import { render } from '@testing-library/react';
import { GoogleAuthProvider } from 'firebase/auth';
import { describe, expect, test, vi } from 'vitest';

import SignInWithGoogleButton from '~/components/tba/auth/signInWithGoogleButton';

const { signInButton } = vi.hoisted(() => ({
  signInButton: vi.fn<(props: Record<string, unknown>) => null>(() => null),
}));

vi.mock('~/components/tba/auth/signInButton', () => ({
  default: signInButton,
}));

describe('SignInWithGoogleButton', () => {
  test('signs in with a Google provider', () => {
    signInButton.mockReturnValue(null);

    render(<SignInWithGoogleButton />);

    const props = signInButton.mock.calls[0][0];
    expect(props.provider).toBeInstanceOf(GoogleAuthProvider);
    expect(props.text).toBe('Sign in with Google');
    expect(props.logo).toEqual(expect.any(String));
  });
});
