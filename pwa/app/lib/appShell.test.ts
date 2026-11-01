import { renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import { isAppShellDocument, useIsHydratingAppShell } from '~/lib/appShell';

const mocks = vi.hoisted(() => ({
  isServer: false,
  isShell: false,
  hydrated: false,
}));

vi.mock('@tanstack/react-router', () => ({
  useRouter: () => ({
    isServer: mocks.isServer,
    isShell: () => mocks.isShell,
  }),
  useHydrated: () => mocks.hydrated,
}));

beforeEach(() => {
  mocks.isServer = false;
  mocks.isShell = false;
  mocks.hydrated = false;
});

afterEach(() => {
  document.documentElement.removeAttribute('data-app-shell');
});

describe('isAppShellDocument', () => {
  test('is true for a document marked as the app shell', () => {
    document.documentElement.setAttribute('data-app-shell', '');

    expect(isAppShellDocument()).toBe(true);
  });

  test('is false for a server-rendered document', () => {
    expect(isAppShellDocument()).toBe(false);
  });
});

describe('useIsHydratingAppShell', () => {
  test('is true while prerendering the app shell', () => {
    mocks.isServer = true;
    mocks.isShell = true;

    const { result } = renderHook(() => useIsHydratingAppShell());

    expect(result.current).toBe(true);
  });

  test('is false while server-rendering a page', () => {
    mocks.isServer = true;

    const { result } = renderHook(() => useIsHydratingAppShell());

    expect(result.current).toBe(false);
  });

  test('is true while hydrating the app shell', () => {
    document.documentElement.setAttribute('data-app-shell', '');

    const { result } = renderHook(() => useIsHydratingAppShell());

    expect(result.current).toBe(true);
  });

  test('is false once the app shell has hydrated', () => {
    document.documentElement.setAttribute('data-app-shell', '');
    mocks.hydrated = true;

    const { result } = renderHook(() => useIsHydratingAppShell());

    expect(result.current).toBe(false);
  });

  test('is false while hydrating a server-rendered page', () => {
    const { result } = renderHook(() => useIsHydratingAppShell());

    expect(result.current).toBe(false);
  });
});
