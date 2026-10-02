import { render, screen, within } from '@testing-library/react';
import { type AnchorHTMLAttributes } from 'react';
import { describe, expect, test, vi } from 'vitest';

import { type PlayoffAdvancement } from '~/api/tba/read';
import PlayoffAdvancement2015Table from '~/components/tba/playoffAdvancement2015Table';

vi.mock('~/components/tba/teamTooltip', () => ({
  TeamLinkWithTooltip: ({
    teamKey,
    year,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement> & {
    teamKey: string;
    year: number;
  }) => (
    <a href={`/team/${teamKey.substring(3)}/${year}`} {...props}>
      {teamKey.substring(3)}
    </a>
  ),
}));

const quarterfinals: PlayoffAdvancement = {
  level: 'qf',
  level_name: 'Quarterfinals',
  type: 'average_score',
  sort_order_info: [{ name: 'Average Score', type: 'int', precision: 2 }],
  extra_stats_info: [{ name: 'Advance to Semis', type: 'bool', precision: 0 }],
  rankings: [
    {
      team_keys: ['frc2337', 'frc1718', 'frc33'],
      alliance_name: 'Alliance 1',
      rank: 1,
      matches_played: 2,
      sort_orders: [151.5],
      extra_stats: [1],
    },
    {
      team_keys: ['frc245', 'frc27', 'frc548'],
      alliance_name: 'Alliance 2',
      rank: 2,
      matches_played: 2,
      sort_orders: [140],
      extra_stats: [0],
    },
  ],
};

const finals: PlayoffAdvancement = {
  level: 'f1',
  level_name: 'Finals',
  type: 'best_of_3',
  sort_order_info: [{ name: 'Wins', type: 'int', precision: 0 }],
  extra_stats_info: [],
  rankings: [],
};

describe('PlayoffAdvancement2015Table', () => {
  test('shows the advancement level heading', () => {
    render(
      <PlayoffAdvancement2015Table
        advancements={[quarterfinals]}
        year={2015}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Quarterfinals' })).toBeTruthy();
  });

  test('links teams to their event-year team pages', () => {
    render(
      <PlayoffAdvancement2015Table
        advancements={[quarterfinals]}
        year={2015}
      />,
    );

    expect(
      screen.getByRole('link', { name: '2337' }).getAttribute('href'),
    ).toBe('/team/2337/2015');
  });

  test('formats the average score using the API precision', () => {
    render(
      <PlayoffAdvancement2015Table
        advancements={[quarterfinals]}
        year={2015}
      />,
    );

    expect(
      within(screen.getByRole('row', { name: /^1 Alliance 1/ })).getByText(
        '151.50',
      ),
    ).toBeTruthy();
  });

  test('marks an advancing alliance', () => {
    render(
      <PlayoffAdvancement2015Table
        advancements={[quarterfinals]}
        year={2015}
      />,
    );

    expect(
      within(screen.getByRole('row', { name: /^1 Alliance 1/ })).getByLabelText(
        'Advance to Semis',
      ),
    ).toBeTruthy();
  });

  test('does not mark a non-advancing alliance', () => {
    render(
      <PlayoffAdvancement2015Table
        advancements={[quarterfinals]}
        year={2015}
      />,
    );

    expect(
      within(
        screen.getByRole('row', { name: /^2 Alliance 2/ }),
      ).queryByLabelText('Advance to Semis'),
    ).toBeNull();
  });

  test('does not render the finals result', () => {
    render(
      <PlayoffAdvancement2015Table
        advancements={[quarterfinals, finals]}
        year={2015}
      />,
    );

    expect(screen.queryByRole('heading', { name: 'Finals' })).toBeNull();
  });

  test('renders nothing without average-score advancement levels', () => {
    render(<PlayoffAdvancement2015Table advancements={[finals]} year={2015} />);

    expect(
      screen.queryByRole('heading', { name: 'Playoff Advancement' }),
    ).toBeNull();
  });
});
