import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  type InsightV2GameStats,
  type InsightV2Leaderboard,
  type InsightV2Streak,
  type InsightV2Timeseries,
} from '~/api/tba/read';
import { InsightSections } from '~/components/tba/insightSections';

vi.mock('~/components/tba/leaderboard', () => ({
  Leaderboard: ({ displayName }: { displayName: string }) => (
    <div>{displayName}</div>
  ),
}));
vi.mock('~/components/tba/streakInsight', () => ({
  StreakInsight: () => <div />,
}));
vi.mock('~/components/tba/successRateInsight', () => ({
  SuccessRateInsight: () => <div />,
}));
vi.mock('~/components/tba/timeseriesInsight', () => ({
  TimeseriesInsight: () => <div />,
}));

const leaderboard = {
  name: 'blue_banners',
  display_name: 'Total Blue Banners',
  year: 2024,
  category: 'leaderboard',
  data: { rankings: [], key_type: 'team' },
} as unknown as InsightV2Leaderboard;

function renderSections({
  leaderboards = [],
  streaks = [],
  timeseries = [],
  successRates = [],
}: {
  leaderboards?: InsightV2Leaderboard[];
  streaks?: InsightV2Streak[];
  timeseries?: InsightV2Timeseries[];
  successRates?: InsightV2GameStats[];
}) {
  render(
    <InsightSections
      year={2024}
      eventsByKey={new Map()}
      leaderboards={leaderboards}
      streaks={streaks}
      timeseries={timeseries}
      successRates={successRates}
    />,
  );
}

describe('InsightSections', () => {
  test('shows the leaderboards heading when there are leaderboards', () => {
    renderSections({ leaderboards: [leaderboard] });
    expect(screen.getByRole('heading', { name: 'Leaderboards' })).toBeTruthy();
  });

  test('omits headings for categories with no insights', () => {
    renderSections({ leaderboards: [leaderboard] });
    expect(screen.getAllByRole('heading')).toHaveLength(1);
  });

  test('shows each leaderboard by its display name', () => {
    renderSections({ leaderboards: [leaderboard] });
    expect(screen.getByText('Total Blue Banners')).toBeTruthy();
  });
});
