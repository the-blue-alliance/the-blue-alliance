import { fireEvent, screen } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { InsightV2, InsightV2GameStatsScope } from '~/api/tba/read';
import { getInsightsV2YearCategory } from '~/api/tba/read/sdk.gen';
import { EventSuccessRateTable } from '~/components/tba/eventSuccessRateTable';
import { mockTbaApi } from '~/test/msw';
import { renderWithClient } from '~/test/render';

function scope(
  overrides: Partial<InsightV2GameStatsScope>,
): InsightV2GameStatsScope {
  return {
    scope_type: 'event',
    label: '2026miket',
    key: '2026miket',
    week: null,
    qual: [{ name: 'climb', label: 'Climb', count: 1, opportunities: 2 }],
    playoff: [{ name: 'climb', label: 'Climb', count: 3, opportunities: 4 }],
    qual_averages: [],
    playoff_averages: [],
    ...overrides,
  };
}

function insights(scopes: InsightV2GameStatsScope[]): InsightV2[] {
  return [
    {
      name: 'most_wins',
      display_name: 'Most Wins',
      year: 2026,
      category: 'leaderboard',
      district_abbreviation: null,
      data: { rankings: [], key_type: 'team', context_type: 'none' },
    },
    {
      name: 'game_stats',
      display_name: 'Game Stats',
      year: 2026,
      category: 'game_stats',
      district_abbreviation: null,
      data: { scopes },
    },
  ];
}

function mockInsights(scopes: InsightV2GameStatsScope[]) {
  return mockTbaApi(
    getInsightsV2YearCategory,
    { path: { year: 2026, category: 'game_stats' } },
    insights(scopes),
  );
}

function renderTable() {
  return renderWithClient(
    <EventSuccessRateTable eventKey="2026miket" year={2026} />,
  );
}

describe('EventSuccessRateTable', () => {
  beforeEach(() => {
    mockInsights([
      scope({ scope_type: 'overall', key: null, label: 'Season' }),
      scope({ key: '2026other' }),
      scope({}),
    ]);
  });

  test("renders this event's scope and switches to playoffs", async () => {
    renderTable();
    expect(
      await screen.findByRole('row', { name: 'Climb 1 2 50.00%' }),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole('tab', { name: 'Playoffs' }));
    expect(screen.getByRole('row', { name: 'Climb 3 4 75.00%' })).toBeTruthy();
  });

  test('renders nothing without a matching scope', async () => {
    const requests = mockInsights([scope({ key: '2026other' })]);
    const { container } = renderTable();
    await vi.waitFor(() => expect(requests).toHaveLength(1));
    await new Promise((r) => setTimeout(r, 0));
    expect(container.innerHTML).toBe('');
  });
});
