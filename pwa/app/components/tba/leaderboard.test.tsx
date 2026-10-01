import { act, fireEvent, render, screen, within } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import { type Event, EventType } from '~/api/tba/read';
import {
  Leaderboard,
  type LeaderboardData,
  type LeaderboardShape,
} from '~/components/tba/leaderboard';

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    params,
    to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children?: ReactNode;
    params: { eventKey: string };
    to: string;
  }) => (
    <a href={to.replace('$eventKey', params.eventKey)} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('~/components/tba/links', () => ({
  TeamLink: ({
    children,
    teamOrKey,
    year,
  }: {
    children?: ReactNode;
    teamOrKey: string;
    year: number;
  }) => <a href={`/team/${teamOrKey}/${year}`}>{children}</a>,
  MatchLink: ({
    children,
    matchOrKey,
    event,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement> & {
    children?: ReactNode;
    matchOrKey: string;
    event?: Event;
  }) => (
    <a href={`/match/${matchOrKey}`} data-event={event?.key} {...props}>
      {children}
    </a>
  ),
}));

const casj = {
  key: '2024casj',
  name: 'Silicon Valley Regional',
  short_name: 'Silicon Valley',
  event_type: EventType.REGIONAL,
  year: 2024,
  city: 'San Jose',
  playoff_type: null,
} as Event;

const eventsByKey = new Map([['2024casj', casj]]);

function leaderboard(data: LeaderboardData): LeaderboardShape {
  return { name: 'most_wins', year: 2024, data };
}

/** Hovers a tooltip trigger and returns the tooltip popup that opens. */
async function hoverTooltip(element: Element | null): Promise<HTMLElement> {
  const trigger = element?.closest('[data-slot="tooltip-trigger"]');
  if (!trigger) {
    throw new Error('No tooltip trigger');
  }
  await act(async () => {
    fireEvent.pointerEnter(trigger, { pointerType: 'mouse' });
    fireEvent.mouseEnter(trigger);
    fireEvent.mouseMove(trigger);
    await new Promise((r) => setTimeout(r, 10));
  });
  const popup = document.querySelector<HTMLElement>(
    '[data-slot="tooltip-content"]',
  );
  if (!popup) {
    throw new Error('No tooltip opened');
  }
  return popup;
}

function rowCells(row: HTMLElement) {
  return within(row)
    .getAllByRole('cell')
    .map((c) => c.textContent);
}

describe('Leaderboard', () => {
  test('renders team rankings with the display name', () => {
    render(
      <Leaderboard
        displayName="Most Wins"
        subtitle="2024"
        year={2024}
        leaderboard={leaderboard({
          key_type: 'team',
          rankings: [{ keys: ['frc254', 'frc604'], value: 12 }],
        })}
      />,
    );
    expect(screen.getByText('Most Wins')).toBeTruthy();
    expect(screen.getByRole('columnheader', { name: 'Team' })).toBeTruthy();
    const row = screen.getAllByRole('row')[1];
    expect(rowCells(row)).toEqual(['12', '254, 604']);
    expect(
      within(row).getByRole('link', { name: '254' }).getAttribute('href'),
    ).toBe('/team/frc254/2024');
  });

  test('falls back to the leaderboard name and expands', () => {
    render(
      <Leaderboard
        year={2024}
        leaderboard={leaderboard({
          key_type: 'team',
          rankings: Array.from({ length: 12 }, (_, i) => ({
            keys: [`frc${i + 1}`],
            value: 12 - i,
          })),
        })}
      />,
    );
    expect(screen.getByText('most_wins')).toBeTruthy();
    expect(screen.getAllByRole('row')).toHaveLength(11);
    fireEvent.click(screen.getByRole('button', { name: 'Toggle' }));
    expect(screen.getAllByRole('row')).toHaveLength(13);
  });

  test('renders events with names and event contexts in tooltips', async () => {
    render(
      <Leaderboard
        year={2024}
        eventsByKey={eventsByKey}
        leaderboard={leaderboard({
          key_type: 'event',
          rankings: [
            {
              keys: ['2024casj', '2024miket'],
              value: 3,
              contexts: [{ event_keys: ['2024casj', '2024miket'] }, {}],
            },
          ],
        })}
      />,
    );
    const row = screen.getAllByRole('row')[1];
    expect(rowCells(row)).toEqual(['3', 'Silicon Valley Regional, 2024miket']);

    const tooltip = await hoverTooltip(
      within(row).getByRole('link', { name: 'Silicon Valley Regional' }),
    );
    expect(tooltip.textContent).toBe('Silicon Valley Regional, 2024miket');
  });

  test('renders match keys with alliance contexts', async () => {
    render(
      <Leaderboard
        year={2024}
        eventsByKey={eventsByKey}
        leaderboard={leaderboard({
          key_type: 'match',
          rankings: [
            {
              keys: ['2024casj_qm1', '2024miket_qm2'],
              value: 200,
              contexts: [
                { match_key: '2024casj_qm1', alliance: ['frc254', 'frc604'] },
                { match_key: '2024miket_qm2', alliance: [] },
              ],
            },
          ],
        })}
      />,
    );
    const row = screen.getAllByRole('row')[1];
    const link = within(row).getByRole('link', {
      name: 'Silicon Valley Regional Quals 1',
    });
    expect(link.dataset.event).toBe('2024casj');
    expect(link.title).toBe('2024casj_qm1');
    expect(
      within(row).getByRole('link', { name: 'Quals 2' }).dataset.event,
    ).toBe(undefined);

    const tooltip = await hoverTooltip(link);
    expect(tooltip.textContent).toBe(
      'Silicon Valley Regional Quals 1 (254, 604)',
    );
  });

  test('renders an empty-alliance match context without teams', async () => {
    render(
      <Leaderboard
        year={2024}
        leaderboard={leaderboard({
          key_type: 'match',
          rankings: [
            {
              keys: ['2024miket_qm2'],
              value: 200,
              contexts: [{ match_key: '2024miket_qm2', alliance: [] }],
            },
          ],
        })}
      />,
    );
    const tooltip = await hoverTooltip(
      screen.getByRole('link', { name: 'Quals 2' }),
    );
    expect(tooltip.textContent).toBe('Quals 2');
  });

  test('uses the context tooltip map for grouped keys', async () => {
    render(
      <Leaderboard
        year={2024}
        contextTooltipMap={{ 'frc254-frc604': 'Won together' }}
        leaderboard={leaderboard({
          key_type: 'team_pair',
          rankings: [
            {
              keys: [
                ['frc254', 'frc604'],
                ['frc1', 'frc2'],
              ],
              value: 4,
            },
          ],
        })}
      />,
    );
    expect(
      screen.getByRole('columnheader', { name: 'Team Pair' }),
    ).toBeTruthy();
    const row = screen.getAllByRole('row')[1];
    expect(rowCells(row)).toEqual(['4', '254 & 604, 1 & 2']);

    const tooltip = await hoverTooltip(
      within(row).getByRole('link', { name: '254' }),
    );
    expect(tooltip.textContent).toBe('Won together');
  });

  test('joins alliance keys with commas and uses a custom renderer', () => {
    render(
      <Leaderboard
        year={2024}
        renderKey={(key) => <b>{key.toUpperCase()}</b>}
        leaderboard={leaderboard({
          key_type: 'alliance',
          rankings: [{ keys: [['frc254', 'frc604', 'frc1']], value: 1 }],
        })}
      />,
    );
    expect(screen.getByRole('columnheader', { name: 'Alliance' })).toBeTruthy();
    expect(rowCells(screen.getAllByRole('row')[1])).toEqual([
      '1',
      'FRC254, FRC604, FRC1',
    ]);
  });

  test('summarizes keys past the cutoff in a tooltip', async () => {
    const keys = Array.from({ length: 22 }, (_, i) => `frc${i + 1}`);
    render(
      <Leaderboard
        year={2024}
        leaderboard={leaderboard({
          key_type: 'team',
          rankings: [{ keys, value: 1 }],
        })}
      />,
    );
    const tooltip = await hoverTooltip(screen.getByText(/and 2 others/));
    expect(within(tooltip).getAllByRole('link')).toHaveLength(22);
    expect(tooltip.textContent).toContain('1, 2, 3');
  });
});
