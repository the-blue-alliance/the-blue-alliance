import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { ThemeProvider, useTheme } from '~/lib/theme';

interface FakeMediaQueryList {
  matches: boolean;
  addEventListener: (type: string, listener: () => void) => void;
  removeEventListener: (type: string, listener: () => void) => void;
}

function installMatchMedia(prefersDark: boolean) {
  const listeners = new Set<() => void>();
  const mediaQueryList: FakeMediaQueryList = {
    matches: prefersDark,
    addEventListener: (_type, listener) => listeners.add(listener),
    removeEventListener: (_type, listener) => listeners.delete(listener),
  };
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    writable: true,
    value: vi.fn<() => FakeMediaQueryList>(() => mediaQueryList),
  });
  return {
    setPrefersDark(value: boolean) {
      mediaQueryList.matches = value;
      listeners.forEach((listener) => listener());
    },
  };
}

function renderTheme() {
  return renderHook(() => useTheme(), { wrapper: ThemeProvider });
}

function storageEvent(key: string, newValue: string) {
  return new StorageEvent('storage', { key, newValue });
}

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
    installMatchMedia(false);
  });

  test('throws when used outside a ThemeProvider', () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);

    expect(() => renderHook(() => useTheme())).toThrow(
      'useTheme must be used within a ThemeProvider',
    );
  });

  test('defaults to the system theme', () => {
    const { result } = renderTheme();

    expect(result.current.theme).toBe('system');
  });

  test('resolves the system theme from the OS dark preference', () => {
    installMatchMedia(true);

    const { result } = renderTheme();

    expect(result.current.resolvedTheme).toBe('dark');
  });

  test('marks the document dark when the OS prefers dark', () => {
    installMatchMedia(true);

    renderTheme();

    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  test('restores a stored theme on mount', () => {
    localStorage.setItem('theme', 'dark');

    const { result } = renderTheme();

    expect(result.current.theme).toBe('dark');
    expect(result.current.resolvedTheme).toBe('dark');
  });

  test('falls back to the system theme for an unrecognised stored value', () => {
    localStorage.setItem('theme', 'purple');

    const { result } = renderTheme();

    expect(result.current.theme).toBe('system');
  });

  test('setTheme persists the choice for the next visit', () => {
    const { result } = renderTheme();

    act(() => result.current.setTheme('light'));

    expect(localStorage.getItem('theme')).toBe('light');
  });

  test('setTheme dark marks the document dark', () => {
    const { result } = renderTheme();

    act(() => result.current.setTheme('dark'));

    expect(result.current.resolvedTheme).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  test('setTheme light clears the dark document marker', () => {
    installMatchMedia(true);
    const { result } = renderTheme();

    act(() => result.current.setTheme('light'));

    expect(result.current.resolvedTheme).toBe('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  test('follows OS preference changes while on the system theme', () => {
    const media = installMatchMedia(false);
    const { result } = renderTheme();

    act(() => media.setPrefersDark(true));

    expect(result.current.resolvedTheme).toBe('dark');
  });

  test('ignores OS preference changes after an explicit theme is chosen', () => {
    const media = installMatchMedia(false);
    const { result } = renderTheme();
    act(() => result.current.setTheme('light'));

    act(() => media.setPrefersDark(true));

    expect(result.current.resolvedTheme).toBe('light');
  });

  test('adopts a theme chosen in another tab', () => {
    const { result } = renderTheme();

    act(() => {
      window.dispatchEvent(storageEvent('theme', 'dark'));
    });

    expect(result.current.theme).toBe('dark');
    expect(result.current.resolvedTheme).toBe('dark');
  });

  test('ignores storage events carrying an unrecognised theme', () => {
    const { result } = renderTheme();

    act(() => {
      window.dispatchEvent(storageEvent('theme', 'neon'));
    });

    expect(result.current.theme).toBe('system');
  });

  test('ignores storage events for other keys', () => {
    const { result } = renderTheme();

    act(() => {
      window.dispatchEvent(storageEvent('other', 'dark'));
    });

    expect(result.current.theme).toBe('system');
  });
});
