import { fireEvent, render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { VideoCell } from '~/components/tba/gameday/VideoCell';
import type { GamedayContent } from '~/lib/gameday/types';

const gamedayMocks = vi.hoisted(() => ({
  addContentAtPosition: vi.fn<(contentId: string, position: number) => void>(),
  removeContent: vi.fn<(contentId: string) => void>(),
  swapPositions: vi.fn<(position1: number, position2: number) => void>(),
}));

const gamedayState = vi.hoisted(() => ({
  layoutId: 3 as number | null,
  availableContent: [] as GamedayContent[],
}));

vi.mock('~/lib/gameday/context', () => ({
  useGameday: () => ({
    state: { layoutId: gamedayState.layoutId },
    availableContent: gamedayState.availableContent,
    ...gamedayMocks,
  }),
}));

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    params,
    to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children: ReactNode;
    params?: Record<string, string>;
    to: string;
  }) => (
    <a
      href={Object.entries(params ?? {}).reduce(
        (href, [key, value]) => href.replace(`$${key}`, value),
        to,
      )}
      {...props}
    >
      {children}
    </a>
  ),
}));

const dataPanel: GamedayContent = {
  type: 'data-panel',
  id: 'data-panel:match-recommendations',
  name: 'Match Recommendations',
  component: () => <p>Recommended match contents</p>,
};

describe('VideoCell data panels', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    gamedayState.layoutId = 3;
    gamedayState.availableContent = [];
  });

  test('renders a data panel as grid content', () => {
    render(<VideoCell position={0} content={dataPanel} gridArea="a" />);

    expect(screen.getByText('Recommended match contents').textContent).toBe(
      'Recommended match contents',
    );
  });

  test('labels a data panel in the cell toolbar', () => {
    render(<VideoCell position={0} content={dataPanel} gridArea="a" />);

    expect(screen.getByText('Match Recommendations').textContent).toBe(
      'Match Recommendations',
    );
  });

  test('removes a data panel through the standard cell control', () => {
    render(<VideoCell position={0} content={dataPanel} gridArea="a" />);

    fireEvent.click(screen.getByRole('button', { name: 'Remove content' }));

    expect(gamedayMocks.removeContent).toHaveBeenCalledWith(
      'data-panel:match-recommendations',
    );
  });
});

const eventWebcast: GamedayContent = {
  type: 'webcast',
  id: '2026mi-ket-0',
  name: 'Kettering #1',
  webcast: {
    id: '2026mi-ket-0',
    name: 'Kettering #1',
    webcast: { type: 'youtube', channel: 'abc123' },
    isSpecial: false,
  },
};

const specialWebcast: GamedayContent = {
  type: 'webcast',
  id: 'fun-0',
  name: 'FUN',
  webcast: {
    id: 'fun-0',
    name: 'FUN',
    webcast: { type: 'twitch', channel: 'funroboticsnetwork' },
    isSpecial: true,
  },
};

describe('VideoCell webcasts and controls', () => {
  beforeEach(() => {
    gamedayState.layoutId = 3;
    gamedayState.availableContent = [];
  });

  test('embeds an event webcast and links to its event', () => {
    render(<VideoCell position={0} content={eventWebcast} gridArea="a" />);

    expect(screen.getByTitle('YouTube video player')).toBeTruthy();
    // Everything before the final "-<number>" is the event key.
    expect(
      screen.getByRole('link', { name: 'Kettering #1' }).getAttribute('href'),
    ).toBe('/event/2026mi-ket');
  });

  test('labels a special webcast without an event link', () => {
    render(<VideoCell position={0} content={specialWebcast} gridArea="a" />);

    expect(screen.getByText('FUN')).toBeTruthy();
    expect(screen.queryByRole('link')).toBeNull();
  });

  test('swaps directly in two-view layouts', () => {
    gamedayState.layoutId = 1;
    render(<VideoCell position={1} content={eventWebcast} gridArea="b" />);

    fireEvent.click(screen.getByRole('button', { name: 'Swap position' }));

    expect(gamedayMocks.swapPositions).toHaveBeenCalledWith(0, 1);
  });

  test('ignores swaps without a layout', () => {
    gamedayState.layoutId = null;
    render(<VideoCell position={0} content={eventWebcast} gridArea="a" />);

    fireEvent.click(screen.getByRole('button', { name: 'Swap position' }));

    expect(gamedayMocks.swapPositions).not.toHaveBeenCalled();
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  test('picks a swap target in larger layouts', () => {
    render(<VideoCell position={0} content={eventWebcast} gridArea="a" />);

    fireEvent.click(screen.getByRole('button', { name: 'Swap position' }));
    fireEvent.click(
      screen.getByRole('button', { name: 'Swap with position 3' }),
    );

    expect(gamedayMocks.swapPositions).toHaveBeenCalledWith(0, 2);
  });

  test('changes the content in a cell', () => {
    gamedayState.availableContent = [specialWebcast];
    render(<VideoCell position={2} content={eventWebcast} gridArea="c" />);

    fireEvent.click(screen.getByRole('button', { name: 'Change content' }));
    fireEvent.click(screen.getByRole('button', { name: 'FUN' }));

    expect(gamedayMocks.addContentAtPosition).toHaveBeenCalledWith('fun-0', 2);
  });

  test('offers content for an empty cell', () => {
    gamedayState.availableContent = [specialWebcast];
    render(<VideoCell position={1} content={null} gridArea="b" />);

    fireEvent.click(screen.getByRole('button', { name: 'Select content' }));

    expect(screen.getByText('Select content', { selector: 'h2' })).toBeTruthy();
  });

  test('disables an empty cell when nothing is available', () => {
    render(<VideoCell position={1} content={null} gridArea="b" />);

    const button = screen.getByRole('button', { name: 'No content available' });
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });
});
