import { describe, expect, test } from 'vitest';

import { type InsightV2Timeseries } from '~/api/tba/read';
import { mergeSeries, timeseriesHasTemporalXAxis } from '~/lib/insightUtils';

type TimeseriesData = InsightV2Timeseries['data'];

function data(overrides: Partial<TimeseriesData>): TimeseriesData {
  return {
    series: [],
    x_type: 'year',
    x_label: 'Year',
    y_label: 'Matches',
    point_context_type: 'none',
    ...overrides,
  };
}

describe.concurrent('timeseriesHasTemporalXAxis', () => {
  test('is false for categorical x-axes', () => {
    expect(timeseriesHasTemporalXAxis(data({ x_type: 'year' }))).toBe(false);
    expect(timeseriesHasTemporalXAxis(data({ x_type: 'week' }))).toBe(false);
    expect(timeseriesHasTemporalXAxis(data({ x_type: 'event' }))).toBe(false);
  });

  test('is true for date-typed series', () => {
    expect(timeseriesHasTemporalXAxis(data({ x_type: 'date' }))).toBe(true);
  });

  test('is true for match-record series regardless of x_type', () => {
    expect(
      timeseriesHasTemporalXAxis(
        data({ x_type: 'year', point_context_type: 'match_record' }),
      ),
    ).toBe(true);
  });
});

describe.concurrent('mergeSeries', () => {
  test('keeps input order for a categorical x-axis', () => {
    const rows = mergeSeries(
      data({
        x_type: 'year',
        series: [
          {
            label: 'Matches',
            points: [
              { x: 2024, y: 5 },
              { x: 2023, y: 3 },
            ],
          },
        ],
      }),
    );
    expect(rows.map((r) => r.x)).toEqual([2024, 2023]);
  });

  test('sorts numerically for a date x-axis', () => {
    const rows = mergeSeries(
      data({
        x_type: 'date',
        x_label: 'Date',
        series: [
          {
            label: 'Matches Played',
            points: [
              { x: 300, y: 9 },
              { x: 100, y: 3 },
              { x: 200, y: 6 },
            ],
          },
        ],
      }),
    );
    expect(rows.map((r) => r.x)).toEqual([100, 200, 300]);
    expect(rows.map((r) => r['Matches Played'])).toEqual([3, 6, 9]);
  });
});
