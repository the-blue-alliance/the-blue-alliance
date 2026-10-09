import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { type Event, type InsightV2 } from '~/api/tba/read';
import { DistrictInsightsTab } from '~/components/tba/districtInsightsTab';

const { insightsFn, eventsFn } = vi.hoisted(() => ({
  insightsFn:
    vi.fn<(year: number, abbreviation: string) => Promise<InsightV2[]>>(),
  eventsFn: vi.fn<(year: number) => Promise<Event[]>>(),
}));

vi.mock('~/api/tba/read/@tanstack/react-query.gen', () => ({
  getInsightsV2YearDistrictOptions: ({
    path,
  }: {
    path: { year: number; district_abbreviation: string };
  }) => ({
    queryKey: ['district-insights', path.year, path.district_abbreviation],
    queryFn: () => insightsFn(path.year, path.district_abbreviation),
  }),
  getEventsByYearOptions: ({ path }: { path: { year: number } }) => ({
    queryKey: ['events', path.year],
    queryFn: () => eventsFn(path.year),
  }),
}));

vi.mock('~/components/tba/leaderboard', () => ({
  Leaderboard: ({ displayName }: { displayName: string }) => (
    <div>{displayName}</div>
  ),
}));

function renderTab() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <DistrictInsightsTab abbreviation="fim" year={2024} />
    </QueryClientProvider>,
  );
}

describe('DistrictInsightsTab', () => {
  beforeEach(() => {
    insightsFn.mockReset();
    eventsFn.mockReset();
    eventsFn.mockResolvedValue([]);
  });

  test('shows an empty message when the district has no insights', async () => {
    insightsFn.mockResolvedValue([]);
    renderTab();
    expect(
      await screen.findByText('No insights for this district in 2024.'),
    ).toBeTruthy();
  });

  test('shows an empty message when the insights request fails', async () => {
    insightsFn.mockRejectedValue(new Error('404'));
    renderTab();
    expect(
      await screen.findByText('No insights for this district in 2024.'),
    ).toBeTruthy();
  });

  test('shows a leaderboard returned for the district', async () => {
    insightsFn.mockResolvedValue([
      {
        name: 'blue_banners',
        display_name: 'Total Blue Banners',
        year: 2024,
        category: 'leaderboard',
        data: { rankings: [], key_type: 'team' },
      } as unknown as InsightV2,
    ]);
    renderTab();
    expect(await screen.findByText('Total Blue Banners')).toBeTruthy();
  });

  test('requests insights for the given year and district', async () => {
    insightsFn.mockResolvedValue([]);
    renderTab();
    await screen.findByText('No insights for this district in 2024.');
    expect(insightsFn).toHaveBeenCalledWith(2024, 'fim');
  });
});
