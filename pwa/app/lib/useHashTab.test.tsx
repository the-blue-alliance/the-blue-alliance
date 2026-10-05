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

// Stand-in for the router: like TanStack's, navigate commits the new hash
// asynchronously, then re-renders location subscribers
const routerListeners = new Set<() => void>();
const navigate = vi.fn<
  (opts: { hash: string; replace?: boolean }) => Promise<void>
>(
  (opts) =>
    new Promise((resolve) => {
      setTimeout(() => {
        window.history.replaceState(null, '', `#${opts.hash}`);
        routerListeners.forEach((l) => l());
        resolve();
      }, 0);
    }),
);

function subscribeToLocation(cb: () => void) {
  routerListeners.add(cb);
  window.addEventListener('hashchange', cb);
  return () => {
    routerListeners.delete(cb);
    window.removeEventListener('hashchange', cb);
  };
}

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => navigate,
  useLocation: <T,>({ select }: { select: (l: { hash: string }) => T }) =>
    select({
      hash: useSyncExternalStore(
        subscribeToLocation,
        () => window.location.hash.slice(1),
        () => '',
      ),
    }),
}));

const mounts = vi.fn<() => void>();

function MountCounter() {
  useEffect(() => {
    mounts();
  }, []);
  return null;
}

function Page({ values = ['results', 'rankings', 'media'] as string[] }) {
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

  test('clicking tabs updates the hash without remounting the page', async () => {
    render(<Page />);

    await act(async () => {
      fireEvent.click(screen.getByRole('tab', { name: 'rankings' }));
    });
    await act(async () => {
      fireEvent.click(screen.getByRole('tab', { name: 'media' }));
    });

    expect([
      window.location.hash,
      selectedTab(),
      mounts.mock.calls.length,
    ]).toEqual(['#media', 'media', 1]);
  });

  test('rapid clicks select the last clicked tab', async () => {
    render(<Page />);

    // Both clicks land before the router commits either navigation
    fireEvent.click(screen.getByRole('tab', { name: 'rankings' }));
    fireEvent.click(screen.getByRole('tab', { name: 'media' }));
    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    expect([window.location.hash, selectedTab()]).toEqual(['#media', 'media']);
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

  test('follows external hash changes such as back/forward', async () => {
    render(<Page />);
    await act(async () => {
      fireEvent.click(screen.getByRole('tab', { name: 'rankings' }));
    });

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
