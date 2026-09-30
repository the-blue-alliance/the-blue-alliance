import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { Navbar } from '~/components/tba/navigation/navbar';
import { NAV_ITEMS_LIST } from '~/lib/navigation/content';

const mocks = vi.hoisted(() => ({
  pathname: '/team/254',
  subscribe: vi.fn<(event: string, listener: () => void) => () => void>(),
  unsubscribe: vi.fn<() => void>(),
  router: {
    subscribe: (event: string, listener: () => void) =>
      mocks.subscribe(event, listener),
  },
}));

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    to,
    params: _params,
    activeProps: _activeProps,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children?: ReactNode;
    to: string;
    params?: unknown;
    activeProps?: unknown;
  }) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
  useLocation: () => ({ pathname: mocks.pathname }),
  useRouter: () => mocks.router,
}));

vi.mock('~/components/tba/globalLoadingProgress', () => ({
  default: () => <div>Loading progress</div>,
}));

vi.mock('~/components/tba/navigation/searchModal', () => ({
  SearchModal: () => <li>Search modal</li>,
}));

function menuToggle() {
  return screen.getByRole('button', { name: 'Toggle Menu' });
}

function mobileLinks() {
  return screen
    .queryAllByRole('link')
    .filter((link) => link.className.includes('animate-navigation-item'));
}

describe('Navbar', () => {
  beforeEach(() => {
    mocks.subscribe.mockReturnValue(mocks.unsubscribe);
  });

  test('renders the logo, desktop links, and a link out of the beta', () => {
    render(<Navbar />);

    expect(screen.getByAltText('The Blue Alliance Logo')).toBeTruthy();
    for (const { title } of NAV_ITEMS_LIST) {
      expect(screen.getAllByText(title).length).toBeGreaterThan(0);
    }
    expect(
      screen.getByRole('link', { name: 'Leave beta' }).getAttribute('href'),
    ).toBe('https://www.thebluealliance.com/team/254');
    expect(screen.getByText('Search modal')).toBeTruthy();
    expect(screen.getByText('Loading progress')).toBeTruthy();
  });

  test('opens the mobile menu on click', async () => {
    render(<Navbar />);
    expect(mobileLinks()).toHaveLength(0);

    fireEvent.click(menuToggle());

    await waitFor(() =>
      expect(mobileLinks()).toHaveLength(NAV_ITEMS_LIST.length),
    );
    expect(mobileLinks()[1].style.animationDelay).toBe('50ms');
  });

  test('does not open the mobile menu on hover', async () => {
    render(<Navbar />);
    fireEvent.pointerEnter(menuToggle(), { pointerType: 'mouse' });
    fireEvent.mouseEnter(menuToggle());
    for (let i = 0; i < 5; i++) {
      fireEvent.mouseMove(menuToggle(), { clientX: 5 + i, clientY: 5 });
      await act(() => new Promise((resolve) => setTimeout(resolve, 60)));
    }

    expect(mobileLinks()).toHaveLength(0);
  });

  test('closes the menu when navigation starts and unsubscribes on unmount', async () => {
    const { unmount } = render(<Navbar />);
    fireEvent.click(menuToggle());
    await waitFor(() => expect(mobileLinks().length).toBeGreaterThan(0));

    expect(mocks.subscribe).toHaveBeenCalledWith(
      'onBeforeNavigate',
      expect.any(Function),
    );
    const onBeforeNavigate = mocks.subscribe.mock.calls[0][1];
    act(() => onBeforeNavigate());

    await waitFor(() => expect(mobileLinks()).toHaveLength(0));

    unmount();
    expect(mocks.unsubscribe).toHaveBeenCalledTimes(1);
  });
});
