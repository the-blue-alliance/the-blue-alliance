import { describe, expect, it } from 'vitest';

import { shouldForceTokenRefresh } from '~/lib/authRefresh';

describe('shouldForceTokenRefresh', () => {
  it('refreshes when the tab is visible and a user is signed in', () => {
    expect(shouldForceTokenRefresh('visible', true)).toBe(true);
  });

  it('does not refresh when no user is signed in', () => {
    expect(shouldForceTokenRefresh('visible', false)).toBe(false);
  });

  it('does not refresh while the tab is hidden', () => {
    expect(shouldForceTokenRefresh('hidden', true)).toBe(false);
  });
});
