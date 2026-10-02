import { describe, expect, test } from 'vitest';

import { type InsightV2Timeseries } from '~/api/tba/read';
import {
  contextKey,
  mergeSeries,
  rankRowClassName,
  rankTextClassName,
  timeseriesHasTemporalXAxis,
} from '~/lib/insightUtils';

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

describe('timeseriesHasTemporalXAxis', () => {
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

describe('mergeSeries', () => {
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

describe('contextKey', () => {
  test('derives the context column from the series label', () => {
    expect(contextKey('High score')).toBe('High score__ctx');
  });
});

describe('mergeSeries with match records', () => {
  const records = data({
    x_type: 'year',
    point_context_type: 'match_record',
    series: [
      {
        label: 'High score',
        points: [
          {
            x: 2024,
            y: 100,
            context: {
              match_key: '2024casj_qm1',
              alliance: ['frc254', 'frc1678', 'frc2056'],
              post_result_time: 1000,
              is_current: false,
            },
          },
          {
            x: 2024,
            y: 120,
            context: {
              match_key: '2024mil_qm5',
              alliance: ['frc604', 'frc2910', 'frc1323'],
              post_result_time: 2000,
              is_current: true,
            },
          },
        ],
      },
    ],
  });

  test('plots each record at the moment it was set', () => {
    expect(mergeSeries(records).map((row) => row.x)).toEqual([1000, 2000]);
  });

  test('records who set the record and when it was beaten', () => {
    expect(mergeSeries(records)[0][contextKey('High score')]).toEqual({
      matchKey: '2024casj_qm1',
      alliance: ['frc254', 'frc1678', 'frc2056'],
      postResultTime: 1000,
      isCurrent: false,
      heldUntilPostResultTime: 2000,
    });
  });

  test('the standing record has not been beaten', () => {
    expect(mergeSeries(records)[1][contextKey('High score')]).toMatchObject({
      isCurrent: true,
      heldUntilPostResultTime: undefined,
    });
  });

  test('falls back to x for a record point without context', () => {
    const rows = mergeSeries(
      data({
        point_context_type: 'match_record',
        series: [{ label: 'High score', points: [{ x: 2024, y: 100 }] }],
      }),
    );

    expect(rows).toEqual([{ x: 2024, 'High score': 100 }]);
  });

  test('leaves a series column out of rows where it has no point', () => {
    const rows = mergeSeries(
      data({
        series: [
          { label: 'A', points: [{ x: 2023, y: 1 }] },
          { label: 'B', points: [{ x: 2024, y: 2 }] },
        ],
      }),
    );

    expect(rows).toEqual([
      { x: 2023, A: 1 },
      { x: 2024, B: 2 },
    ]);
  });
});

describe('rank accents', () => {
  test.each([1, 2, 3])('podium rank %i rows are accented', (rank) => {
    expect(rankRowClassName(rank)).toBeDefined();
  });

  test('rows below the podium are not accented', () => {
    expect(rankRowClassName(4)).toBeUndefined();
  });

  test('each podium rank has its own row accent', () => {
    expect(
      new Set([rankRowClassName(1), rankRowClassName(2), rankRowClassName(3)])
        .size,
    ).toBe(3);
  });

  test.each([1, 2, 3])('podium rank %i text is accented', (rank) => {
    expect(rankTextClassName(rank)).toBeDefined();
  });

  test('text below the podium is not accented', () => {
    expect(rankTextClassName(4)).toBeUndefined();
  });
});
