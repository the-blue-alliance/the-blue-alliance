import { screen } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import {
  getEventsByYear,
  getInsightsV2YearDistrict,
} from '~/api/tba/read/sdk.gen';
import { DistrictInsightsTab } from '~/components/tba/districtInsightsTab';
import { mockTbaApi, mockTbaApiWith } from '~/test/msw';
import { renderWithClient } from '~/test/render';

vi.mock('~/components/tba/leaderboard', () => ({
  Leaderboard: ({ displayName }: { displayName: string }) => (
    <div>{displayName}</div>
  ),
}));

const INSIGHTS_PATH = { path: { year: 2024, district_abbreviation: 'fim' } };

function renderTab() {
  renderWithClient(<DistrictInsightsTab abbreviation="fim" year={2024} />);
}

describe('DistrictInsightsTab', () => {
  beforeEach(() => {
    mockTbaApi(getEventsByYear, { path: { year: 2024 } }, []);
  });

  test('shows an empty message when the district has no insights', async () => {
    mockTbaApi(getInsightsV2YearDistrict, INSIGHTS_PATH, []);
    renderTab();
    expect(
      await screen.findByText('No insights for this district in 2024.'),
    ).toBeTruthy();
  });

  test('shows an empty message when the insights request fails', async () => {
    mockTbaApiWith(
      getInsightsV2YearDistrict,
      INSIGHTS_PATH,
      () => new HttpResponse(null, { status: 404 }),
    );
    renderTab();
    expect(
      await screen.findByText('No insights for this district in 2024.'),
    ).toBeTruthy();
  });

  test('shows a leaderboard returned for the district', async () => {
    mockTbaApi(getInsightsV2YearDistrict, INSIGHTS_PATH, [
      {
        name: 'blue_banners',
        display_name: 'Total Blue Banners',
        year: 2024,
        category: 'leaderboard',
        district_abbreviation: 'fim',
        data: { rankings: [], key_type: 'team', context_type: 'none' },
      },
    ]);
    renderTab();
    expect(await screen.findByText('Total Blue Banners')).toBeTruthy();
  });
});
