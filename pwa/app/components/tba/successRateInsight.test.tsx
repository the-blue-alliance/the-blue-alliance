import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import type {
  InsightV2GameStats,
  InsightV2GameStatsScope,
} from '~/api/tba/read';
import {
  GameStatsScopeContent,
  SuccessRateInsight,
} from '~/components/tba/successRateInsight';

function makeScope(
  overrides: Partial<InsightV2GameStatsScope> = {},
): InsightV2GameStatsScope {
  return {
    scope_type: 'overall',
    label: 'Season',
    key: null,
    week: null,
    qual: [
      { name: 'climb', label: 'Climb', count: 1234, opportunities: 2000 },
      { name: 'none', label: 'Never', count: 0, opportunities: 0 },
    ],
    playoff: [
      { name: 'climb', label: 'Playoff Climb', count: 5, opportunities: 10 },
    ],
    qual_averages: [{ name: 'score', label: 'Avg Score', value: 87.25 }],
    playoff_averages: [],
    ...overrides,
  };
}

function makeInsight(scopes: InsightV2GameStatsScope[]): InsightV2GameStats {
  return {
    name: 'game_stats',
    display_name: 'Game Stats',
    year: 2026,
    category: 'game_stats',
    district_abbreviation: null,
    data: { scopes },
  };
}

describe('SuccessRateInsight', () => {
  test('renders nothing when only event scopes exist', () => {
    const { container } = render(
      <SuccessRateInsight
        insight={makeInsight([makeScope({ scope_type: 'event' })])}
      />,
    );
    expect(container.innerHTML).toBe('');
  });

  test('switches match level and scope', async () => {
    render(
      <SuccessRateInsight
        subtitle="2026 season"
        insight={makeInsight([
          makeScope(),
          makeScope({ scope_type: 'event', label: 'Some Event' }),
          makeScope({
            scope_type: 'week',
            label: 'Week 1',
            week: 1,
            qual: [
              {
                name: 'climb',
                label: 'Week Climb',
                count: 1,
                opportunities: 4,
              },
            ],
          }),
        ])}
      />,
    );
    expect(screen.getByText('Game Stats')).toBeTruthy();
    expect(screen.getByText('2026 season')).toBeTruthy();
    expect(
      screen.getByRole('row', { name: 'Climb 1,234 2,000 61.70%' }),
    ).toBeTruthy();
    const never = screen.getByRole('row', { name: 'Never 0 0 —' });
    expect(never.lastElementChild?.className).toContain(
      'text-muted-foreground',
    );
    expect(screen.getByRole('row', { name: 'Avg Score 87.3' })).toBeTruthy();
    expect(screen.getByRole('separator')).toBeTruthy();

    fireEvent.click(screen.getByRole('tab', { name: 'Playoffs' }));
    expect(
      screen.getByRole('row', { name: 'Playoff Climb 5 10 50.00%' }),
    ).toBeTruthy();
    expect(screen.queryByRole('separator')).toBeNull();

    fireEvent.click(screen.getByRole('combobox'));
    const week = await screen.findByRole('option', { name: 'Week 1' });
    fireEvent.keyDown(week, { key: 'Enter' });
    fireEvent.click(screen.getByRole('tab', { name: 'Quals' }));
    expect(
      await screen.findByRole('row', { name: 'Week Climb 1 4 25.00%' }),
    ).toBeTruthy();
    expect(screen.queryByText('Some Event')).toBeNull();
  });
});

describe('GameStatsScopeContent', () => {
  test('points to the other tab when only it has data', () => {
    const { container } = render(
      <GameStatsScopeContent
        scope={makeScope({ playoff: [], playoff_averages: [] })}
        matchLevel="playoff"
      />,
    );
    expect(container.textContent).toBe(
      'No playoff match data for Season. Try the Quals tab.',
    );
  });

  test('points to playoffs when quals are empty', () => {
    const { container } = render(
      <GameStatsScopeContent
        scope={makeScope({ qual: [], qual_averages: [] })}
        matchLevel="qual"
      />,
    );
    expect(container.textContent).toBe(
      'No qualification match data for Season. Try the Playoffs tab.',
    );
  });

  test('omits the hint when neither level has data', () => {
    const { container } = render(
      <GameStatsScopeContent
        scope={makeScope({
          qual: [],
          qual_averages: [],
          playoff: [],
          playoff_averages: [],
        })}
        matchLevel="qual"
      />,
    );
    expect(container.textContent).toBe(
      'No qualification match data for Season.',
    );
  });

  test('renders only averages when there are no rates', () => {
    render(
      <GameStatsScopeContent
        scope={makeScope({
          playoff: [],
          playoff_averages: [{ name: 'score', label: 'Avg', value: 3 }],
        })}
        matchLevel="playoff"
      />,
    );
    expect(screen.getAllByRole('table')).toHaveLength(1);
    expect(screen.getByRole('row', { name: 'Avg 3.0' })).toBeTruthy();
  });
});
