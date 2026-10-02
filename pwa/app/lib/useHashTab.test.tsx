import { act, fireEvent, render, screen } from '@testing-library/react';
import { useEffect, useSyncExternalStore } from 'react';
import { hydrateRoot } from 'react-dom/client';
import { renderToString } from 'react-dom/server';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import {
  AnimatedTabs,
  AnimatedTabsTrigger,
} from '~/components/ui/animated-tabs';
import { TabsContent, TabsList } from '~/components/ui/tabs';
import { useHashTab } from '~/lib/useHashTab';

// Stand-in for the router: navigate replaces the hash and re-renders subscribers
const routerListeners = new Set<() => void>();
let routerVersion = 0;
const navigate = vi.fn<
  (opts: { hash: string; replace?: boolean }) => Promise<void>
>((opts) => {
  window.history.replaceState(null, '', `#${opts.hash}`);
  routerVersion += 1;
  routerListeners.forEach((l) => l());
  return Promise.resolve();
});

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => navigate,
}));

function useRouterRerender() {
  return useSyncExternalStore(
    (cb) => {
      routerListeners.add(cb);
      return () => routerListeners.delete(cb);
    },
    () => routerVersion,
    () => routerVersion,
  );
}

const mounts = vi.fn<() => void>();

function MountCounter() {
  useEffect(() => {
    mounts();
  }, []);
  return null;
}

function Page({ values = ['results', 'rankings', 'media'] as string[] }) {
  useRouterRerender();
  const tabs = useHashTab({
    values,
    defaultValue: 'results',
    legacyHashes: { 'old-media': 'media' },
  });
  return (
    <AnimatedTabs {...tabs}>
      <MountCounter />
      <TabsList>
        {values.map((v) => (
          <AnimatedTabsTrigger key={v} value={v}>
            {v}
          </AnimatedTabsTrigger>
        ))}
      </TabsList>
      {values.map((v) => (
        <TabsContent key={v} value={v}>
          {v} panel
        </TabsContent>
      ))}
    </AnimatedTabs>
  );
}

function selectedTab() {
  return screen.getByRole('tab', { selected: true }).textContent;
}

describe('useHashTab', () => {
  beforeEach(() => {
    window.history.replaceState(null, '', '/');
    mounts.mockClear();
    navigate.mockClear();
  });
  afterEach(() => {
    window.history.replaceState(null, '', '/');
  });

  test('clicking tabs updates the hash without remounting the page', () => {
    render(<Page />);
    expect(selectedTab()).toBe('results');

    fireEvent.click(screen.getByRole('tab', { name: 'rankings' }));
    expect(window.location.hash).toBe('#rankings');
    expect(selectedTab()).toBe('rankings');

    fireEvent.click(screen.getByRole('tab', { name: 'media' }));
    expect(window.location.hash).toBe('#media');
    expect(selectedTab()).toBe('media');

    expect(navigate).toHaveBeenLastCalledWith(
      expect.objectContaining({ hash: 'media', replace: true }),
    );
    expect(mounts).toHaveBeenCalledTimes(1);
  });

  test('opens the tab named by the hash on load', () => {
    window.history.replaceState(null, '', '/#rankings');
    render(<Page />);
    expect(selectedTab()).toBe('rankings');
  });

  test('maps legacy hashes and ignores unknown ones', () => {
    window.history.replaceState(null, '', '/#old-media');
    const { unmount } = render(<Page />);
    expect(selectedTab()).toBe('media');
    unmount();

    window.history.replaceState(null, '', '/#nope');
    render(<Page />);
    expect(selectedTab()).toBe('results');
  });

  test('follows external hash changes such as back/forward', () => {
    render(<Page />);
    fireEvent.click(screen.getByRole('tab', { name: 'rankings' }));

    act(() => {
      window.history.replaceState(null, '', '/#media');
      window.dispatchEvent(new HashChangeEvent('hashchange'));
    });
    expect(selectedTab()).toBe('media');
    expect(mounts).toHaveBeenCalledTimes(1);
  });

  test('a hash naming a tab that appears later selects it once it appears', () => {
    window.history.replaceState(null, '', '/#late');
    const { rerender } = render(<Page values={['results']} />);
    expect(selectedTab()).toBe('results');

    rerender(<Page values={['results', 'late']} />);
    expect(selectedTab()).toBe('late');
  });

  test('hydrates on the default tab, then switches to the hash without a mismatch', async () => {
    const container = document.createElement('div');
    container.innerHTML = renderToString(<Page />);
    document.body.appendChild(container);
    window.history.replaceState(null, '', '/#rankings');
    const consoleError = vi.spyOn(console, 'error');

    await act(async () => {
      hydrateRoot(container, <Page />);
    });

    expect(selectedTab()).toBe('rankings');
    expect(consoleError).not.toHaveBeenCalled();
    expect(mounts).toHaveBeenCalledTimes(1);
    consoleError.mockRestore();
    container.remove();
  });
});
