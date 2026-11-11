import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import LoginPage from '~/components/tba/auth/loginPage';

vi.mock('@tanstack/react-router', () => import('~/testing/mocks/router'));

vi.mock('~/components/tba/auth/signInWithGoogleButton', () => ({
  default: () => <button>Sign in with Google</button>,
}));

vi.mock('~/components/tba/auth/signInWithAppleButton', () => ({
  default: () => <button>Sign in with Apple</button>,
}));

describe('LoginPage', () => {
  test('offers both sign-in providers and explains accounts', () => {
    render(<LoginPage />);

    expect(
      screen.getByRole('heading', {
        name: 'Please log in to your TBA Account',
      }),
    ).toBeTruthy();
    expect(
      screen.getByRole('button', { name: 'Sign in with Google' }),
    ).toBeTruthy();
    expect(
      screen.getByRole('button', { name: 'Sign in with Apple' }),
    ).toBeTruthy();
    expect(
      screen
        .getByRole('link', { name: 'API documentation' })
        .getAttribute('href'),
    ).toBe('/apidocs');
    expect(
      screen.getByRole('link', { name: 'Android app' }).getAttribute('href'),
    ).toContain('com.thebluealliance.androidclient');
    expect(screen.getByRole('heading', { name: 'myTBA' })).toBeTruthy();
  });
});
