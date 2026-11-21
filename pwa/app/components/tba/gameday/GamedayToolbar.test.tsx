import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { GamedayToolbar } from '~/components/tba/gameday/GamedayToolbar';
import { Layout } from '~/lib/gameday/layouts';

const mocks = vi.hoisted(() => ({
  useGameday: vi.fn<() => unknown>(),
  setLayout: vi.fn<(layoutId: number) => void>(),
  toggleChatSidebar: vi.fn<() => void>(),
  resetContent: vi.fn<() => void>(),
}));

vi.mock('~/lib/gameday/context', () => ({ useGameday: mocks.useGameday }));

function renderToolbar(layoutId: number | null, chatSidebarVisible = true) {
  mocks.useGameday.mockReturnValue({
    state: { layoutId, chatSidebarVisible },
    setLayout: mocks.setLayout,
    toggleChatSidebar: mocks.toggleChatSidebar,
    resetContent: mocks.resetContent,
  });
  return render(<GamedayToolbar />);
}

function openDrawer() {
  fireEvent.click(screen.getByRole('button', { name: /Configure Layout/ }));
}

describe('GamedayToolbar', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn<(query: string) => MediaQueryList>(
        () =>
          ({
            matches: false,
            addEventListener: () => undefined,
            removeEventListener: () => undefined,
          }) as unknown as MediaQueryList,
      ),
    );
  });

  test('links home and shows the current layout icon', () => {
    const { container } = renderToolbar(Layout.QUAD_VIEW);

    expect(screen.getByRole('link').getAttribute('href')).toBe('/');
    expect(screen.getByAltText('TBA')).toBeTruthy();
    expect(container.querySelector('header svg')).toBeTruthy();
  });

  test('omits the layout icon before a layout is chosen', () => {
    const { container } = renderToolbar(null);

    expect(container.querySelector('header button svg')).toBeNull();
  });

  test('marks the current layout and switches layouts', async () => {
    renderToolbar(Layout.QUAD_VIEW);
    openDrawer();

    expect(await screen.findByText('Configure GameDay')).toBeTruthy();
    const quad = screen.getByRole('button', { name: 'Quad View' });
    expect(quad.className).toContain('border-primary');
    expect(
      screen.getByRole('button', { name: 'Single View' }).className,
    ).toContain('border-border');

    fireEvent.click(screen.getByRole('button', { name: 'Single View' }));

    expect(mocks.setLayout).toHaveBeenCalledWith(Layout.SINGLE_VIEW);
  });

  test('toggles the chat sidebar', async () => {
    renderToolbar(Layout.QUAD_VIEW);
    openDrawer();

    const toggle = await screen.findByRole('button', { name: /Twitch Chat/ });
    expect(toggle.textContent).toContain('Visible');
    fireEvent.click(toggle);

    expect(mocks.toggleChatSidebar).toHaveBeenCalledTimes(1);
  });

  test('labels a hidden chat sidebar', async () => {
    renderToolbar(Layout.QUAD_VIEW, false);
    openDrawer();

    expect(
      (await screen.findByRole('button', { name: /Twitch Chat/ })).textContent,
    ).toContain('Hidden');
  });

  test('resets all content', async () => {
    renderToolbar(Layout.QUAD_VIEW);
    openDrawer();

    fireEvent.click(
      await screen.findByRole('button', { name: /Reset All Content/ }),
    );

    expect(mocks.resetContent).toHaveBeenCalledTimes(1);
  });
});
