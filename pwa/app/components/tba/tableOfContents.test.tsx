import { act, fireEvent, render, screen, within } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { useEffect, useState } from 'react';
import {
  mockIsIntersecting,
  setupIntersectionMocking,
} from 'react-intersection-observer/test-utils';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import {
  TOCRendererProvider,
  TableOfContents,
  TableOfContentsSection,
  type TocNode,
} from '~/components/tba/tableOfContents';

const { router } = vi.hoisted(() => ({
  router: {
    listeners: [] as Array<() => void>,
    unsubscribe: vi.fn<() => void>(),
  },
}));

vi.mock('@tanstack/react-router', () => ({
  useRouter: () => ({
    subscribe: (_event: string, listener: () => void) => {
      router.listeners.push(listener);
      return router.unsubscribe;
    },
  }),
  Link: ({
    children,
    hash,
    replace: _replace,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children?: ReactNode;
    hash: string;
    replace?: boolean;
  }) => (
    <a href={`#${hash}`} {...props}>
      {children}
    </a>
  ),
}));

const tocItems: TocNode[] = [
  { slug: 'info', label: 'Info' },
  {
    slug: 'results',
    label: 'Results',
    children: [
      { slug: 'quals', label: 'Quals' },
      { slug: 'playoffs', label: 'Playoffs' },
    ],
  },
];

const scrollIntoView = vi.fn<(options?: ScrollIntoViewOptions) => void>();

beforeEach(() => {
  router.listeners = [];
  Element.prototype.scrollIntoView = scrollIntoView;
});

afterEach(() => {
  Reflect.deleteProperty(Element.prototype, 'scrollIntoView');
});

function linkClass(container: HTMLElement, name: string) {
  return within(container).getByRole('link', { name }).className;
}

describe('TableOfContents', () => {
  test('renders desktop and mobile TOCs with the active section', async () => {
    const { container, unmount } = render(
      <TOCRendererProvider>
        <div data-testid="page">
          <TableOfContents tocItems={tocItems} inView={new Set(['playoffs'])}>
            <span>extra</span>
          </TableOfContents>
        </div>
      </TOCRendererProvider>,
    );
    const desktop = screen.getByTestId('page');
    expect(within(desktop).getByText('extra')).toBeTruthy();
    expect(linkClass(desktop, 'Playoffs')).toContain('font-bold');
    expect(linkClass(desktop, 'Results')).toContain('font-bold');
    expect(linkClass(desktop, 'Quals')).toContain('text-muted-foreground');
    expect(linkClass(desktop, 'Info')).toContain('text-muted-foreground');

    // The mobile header is portaled to the provider, ahead of the page.
    const trigger = await screen.findByRole('button', { name: 'Playoffs' });
    expect(container.firstElementChild?.contains(trigger)).toBe(true);

    fireEvent.click(trigger);
    const popover = await screen.findByRole('dialog');
    const target = document.createElement('div');
    target.id = 'quals';
    document.body.appendChild(target);
    fireEvent.click(within(popover).getByRole('link', { name: 'Quals' }));
    expect(scrollIntoView).toHaveBeenCalledWith({
      behavior: 'instant',
      block: 'start',
    });
    await vi.waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    target.remove();

    unmount();
    expect(router.unsubscribe).toHaveBeenCalled();
  });

  test('closes the mobile popover on navigation', async () => {
    render(
      <TOCRendererProvider>
        <TableOfContents tocItems={tocItems} inView={new Set()} mobileOnly />
      </TOCRendererProvider>,
    );
    // No section is in view, so the trigger has no label.
    expect(screen.queryAllByRole('link')).toHaveLength(0);
    const trigger = await screen.findByRole('button');
    expect(trigger.textContent).toBe('');

    fireEvent.click(trigger);
    expect(await screen.findByRole('dialog')).toBeTruthy();
    act(() => {
      router.listeners.forEach((listener) => listener());
    });
    await vi.waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  });

  test('clicking a desktop link without a target does not scroll', () => {
    render(
      <TableOfContents
        tocItems={[{ slug: '', label: 'Blank' }, ...tocItems]}
        inView={new Set(['info'])}
      />,
    );
    fireEvent.click(screen.getByRole('link', { name: 'Info' }));
    expect(scrollIntoView).not.toHaveBeenCalled();
  });

  test('clears the mobile header when unmounted', async () => {
    function Harness() {
      const [show, setShow] = useState(true);
      return (
        <TOCRendererProvider>
          <button onClick={() => setShow(false)}>hide</button>
          {show && (
            <TableOfContents tocItems={tocItems} inView={new Set(['info'])} />
          )}
        </TOCRendererProvider>
      );
    }
    render(<Harness />);
    expect(await screen.findByRole('button', { name: 'Info' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'hide' }));
    expect(screen.queryByRole('button', { name: 'Info' })).toBeNull();
  });
});

describe('TableOfContentsSection', () => {
  beforeEach(() => {
    setupIntersectionMocking(vi.fn);
  });

  test('tracks whether the section is in view', async () => {
    const latest = { current: new Set<string>() };
    function Harness() {
      const [inView, setInView] = useState<Set<string>>(new Set());
      useEffect(() => {
        latest.current = inView;
      }, [inView]);
      return (
        <TableOfContentsSection
          id="info"
          setInView={setInView}
          className="mt-7"
        >
          Info
        </TableOfContentsSection>
      );
    }
    render(<Harness />);
    const section = screen.getByText('Info');
    expect(section.tagName).toBe('SECTION');
    expect(section.className).toContain('mt-7');

    act(() => {
      mockIsIntersecting(section, true);
    });
    await vi.waitFor(() => expect(latest.current.has('info')).toBe(true));

    act(() => {
      mockIsIntersecting(section, false);
    });
    await vi.waitFor(() => expect(latest.current.has('info')).toBe(false));
  });
});
