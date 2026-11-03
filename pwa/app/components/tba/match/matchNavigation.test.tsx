import { render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import { CompLevel, type Match, PlayoffType } from '~/api/tba/read';
import MatchNavigation from '~/components/tba/match/matchNavigation';

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    params,
    to: _to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children?: ReactNode;
    to: string;
    params: { matchKey: string };
  }) => (
    <a href={`/match/${params.matchKey}`} {...props}>
      {children}
    </a>
  ),
}));

function makeMatch(
  key: string,
  comp_level: CompLevel,
  set_number: number,
  match_number: number,
): Match {
  return {
    key,
    comp_level,
    set_number,
    match_number,
    event_key: '2024casj',
  } as Match;
}

const matches = [
  makeMatch('2024casj_f1m1', CompLevel.F, 1, 1),
  makeMatch('2024casj_qm2', CompLevel.QM, 1, 2),
  makeMatch('2024casj_sf1m1', CompLevel.SF, 1, 1),
  makeMatch('2024casj_qm1', CompLevel.QM, 1, 1),
];

function renderNavigation(matchKey: string) {
  render(
    <MatchNavigation
      matchKey={matchKey}
      matches={matches}
      isPending={false}
      playoffType={PlayoffType.DOUBLE_ELIM_8_TEAM}
    />,
  );
}

describe('MatchNavigation', () => {
  test('links to the previous match in play order', () => {
    renderNavigation('2024casj_sf1m1');

    expect(
      screen
        .getByRole('link', { name: 'Previous match: Quals 2' })
        .getAttribute('href'),
    ).toBe('/match/2024casj_qm2');
  });

  test('links to the next match in play order', () => {
    renderNavigation('2024casj_qm2');

    expect(
      screen
        .getByRole('link', { name: 'Next match: Match 1' })
        .getAttribute('href'),
    ).toBe('/match/2024casj_sf1m1');
  });

  test('has no previous link on the first match', () => {
    renderNavigation('2024casj_qm1');

    expect(screen.queryByRole('link', { name: /^Previous match/ })).toBeNull();
  });

  test('has no next link on the last match', () => {
    renderNavigation('2024casj_f1m1');

    expect(screen.queryByRole('link', { name: /^Next match/ })).toBeNull();
  });

  test('shows a skeleton while the event matches load', () => {
    render(
      <MatchNavigation
        matchKey="2024casj_qm1"
        matches={undefined}
        isPending
        playoffType={PlayoffType.DOUBLE_ELIM_8_TEAM}
      />,
    );

    expect(
      screen.getByRole('status', { name: 'Loading adjacent matches' }),
    ).toBeTruthy();
  });

  test('renders nothing when the match is not in the event list', () => {
    render(
      <MatchNavigation
        matchKey="2024casj_qm1"
        matches={[]}
        isPending={false}
        playoffType={PlayoffType.DOUBLE_ELIM_8_TEAM}
      />,
    );

    expect(
      screen.queryByRole('navigation', { name: 'Event matches' }),
    ).toBeNull();
  });
});
