import { act, fireEvent, render, screen } from '@testing-library/react';
import {
  type ReactElement,
  type ReactNode,
  cloneElement,
  isValidElement,
} from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { InsightV2Timeseries } from '~/api/tba/read';
import { TimeseriesInsight } from '~/components/tba/timeseriesInsight';
import type { ChartRow } from '~/lib/insightUtils';

interface ClickState {
  activeLabel?: string | number;
  activeCoordinate?: { x: number; y: number };
}

// recharts needs real layout to draw anything, so the chart primitives are
// replaced with stand-ins that expose the props the component passes them.
const { chart } = vi.hoisted(() => ({
  chart: {
    onClick: undefined as ((state: ClickState) => void) | undefined,
    tooltipActive: true,
    tooltipPayload: [] as Array<{ payload?: ChartRow }>,
  },
}));

vi.mock('recharts', () => ({
  LineChart: ({
    children,
    onClick,
  }: {
    children: ReactNode;
    onClick: (state: ClickState) => void;
  }) => {
    chart.onClick = onClick;
    return <div data-testid="line-chart">{children}</div>;
  },
  CartesianGrid: () => null,
  XAxis: ({
    type,
    label,
    tickFormatter,
  }: {
    type: string;
    label: { value: string };
    tickFormatter?: (x: number) => string;
  }) => (
    <div data-testid="x-axis" data-type={type} data-label={label.value}>
      {tickFormatter
        ? `${tickFormatter(1700000000)}|${tickFormatter(NaN)}`
        : 'none'}
    </div>
  ),
  YAxis: ({ label }: { label: { value: string } }) => (
    <div data-testid="y-axis">{label.value}</div>
  ),
  Line: ({
    dataKey,
    stroke,
    dot,
  }: {
    dataKey: string;
    stroke: string;
    dot: boolean;
  }) => (
    <div
      data-testid="line"
      data-key={dataKey}
      data-stroke={stroke}
      data-dot={String(dot)}
    />
  ),
}));

vi.mock('~/components/ui/chart', () => ({
  ChartContainer: ({ children }: { children: ReactNode }) => (
    <div>{children}</div>
  ),
  ChartTooltip: ({ content }: { content: ReactElement }) => (
    <div data-testid="chart-tooltip">
      {isValidElement(content)
        ? cloneElement(content as ReactElement<Record<string, unknown>>, {
            active: chart.tooltipActive,
            payload: chart.tooltipPayload,
          })
        : null}
    </div>
  ),
  ChartTooltipContent: ({
    labelFormatter,
    payload,
  }: {
    labelFormatter?: (label: unknown, payload: unknown) => ReactNode;
    payload?: unknown;
  }) => (
    <span data-testid="tooltip-label">
      {labelFormatter ? labelFormatter('', payload) : 'default'}
    </span>
  ),
}));

vi.mock('~/components/tba/links', () => ({
  TeamLink: ({ children }: { children: ReactNode }) => (
    <a href="#t">{children}</a>
  ),
  MatchLink: ({ children }: { children: ReactNode }) => (
    <a href="#m">{children}</a>
  ),
}));

type Data = InsightV2Timeseries['data'];
type Series = Data['series'][number];

function timeseries(data: Partial<Data>): InsightV2Timeseries {
  return {
    name: 'max_score',
    display_name: 'Max Score',
    year: 2024,
    category: 'timeseries',
    district_abbreviation: null,
    data: {
      x_type: 'year',
      x_label: 'Year',
      y_label: 'Score',
      point_context_type: 'none',
      series: [],
      ...data,
    },
  };
}

const T = 1700000000; // Nov 14, 2023 UTC

function recordSeries(label: string, points: Series['points']): Series {
  return { label, points };
}

const recordData: Partial<Data> = {
  x_type: 'year',
  point_context_type: 'match_record',
  series: [
    recordSeries('High', [
      {
        x: 2023,
        y: 100,
        context: {
          match_key: '2023casj_qm1',
          alliance: ['frc254', 'frc604'],
          post_result_time: T,
        },
      },
      {
        x: 2023,
        y: 150,
        context: {
          match_key: '2023casj_qm9',
          alliance: [],
          post_result_time: T + 2 * 86400,
          is_current: true,
        },
      },
    ]),
  ],
};

beforeEach(() => {
  chart.onClick = undefined;
  chart.tooltipActive = true;
  chart.tooltipPayload = [];
});

function click(state: ClickState) {
  act(() => {
    chart.onClick?.(state);
  });
}

/** A copy whose series is a new array, so memoized chart children re-render. */
function freshRecordTimeseries(): InsightV2Timeseries {
  return timeseries({ ...recordData, series: [...(recordData.series ?? [])] });
}

describe('TimeseriesInsight', () => {
  test('renders a categorical chart without record features', () => {
    const series = Array.from({ length: 6 }, (_, i) => ({
      label: `S${i}`,
      points: [{ x: '2024', y: i }],
    }));
    render(
      <TimeseriesInsight
        subtitle="By year"
        timeseries={timeseries({ series })}
      />,
    );
    expect(screen.getByText('Max Score')).toBeTruthy();
    expect(screen.getByText('By year')).toBeTruthy();
    const axis = screen.getByTestId('x-axis');
    expect(axis.dataset.type).toBe('category');
    expect(axis.dataset.label).toBe('Year');
    expect(axis.textContent).toBe('none');
    expect(screen.getByTestId('y-axis').textContent).toBe('Score');
    expect(screen.getAllByTestId('line').map((l) => l.dataset.stroke)).toEqual([
      'var(--color-brand)',
      'var(--color-chart-2)',
      'var(--color-chart-3)',
      'var(--color-chart-4)',
      'var(--color-chart-5)',
      'var(--color-brand)',
    ]);
    expect(screen.getAllByTestId('line')[0].dataset.dot).toBe('false');
    expect(screen.getByTestId('tooltip-label').textContent).toBe('default');

    // Clicking only pins points on record charts.
    click({ activeLabel: '2024', activeCoordinate: { x: 1, y: 2 } });
    expect(screen.getByTestId('chart-tooltip')).toBeTruthy();
  });

  test('formats dates on a date axis', () => {
    chart.tooltipPayload = [{ payload: { x: T } }];
    const { rerender } = render(
      <TimeseriesInsight
        timeseries={timeseries({
          x_type: 'date',
          series: [recordSeries('A', [{ x: T, y: 1 }])],
        })}
      />,
    );
    const axis = screen.getByTestId('x-axis');
    expect(axis.dataset.type).toBe('number');
    expect(axis.textContent).toBe('Nov 14, 2023|');
    expect(screen.getByTestId('tooltip-label').textContent).toBe(
      'Nov 14, 2023',
    );

    chart.tooltipPayload = [];
    rerender(
      <TimeseriesInsight
        timeseries={timeseries({
          x_type: 'date',
          series: [recordSeries('B', [{ x: T, y: 1 }])],
        })}
      />,
    );
    expect(screen.getByTestId('tooltip-label').textContent).toBe('');
  });

  test('shows who set each record and how long it was held', () => {
    const labels = ['Days', 'Hours', 'Minutes', 'Seconds', 'Current', 'Bare'];
    chart.tooltipPayload = [
      {
        payload: {
          x: T,
          Days: 1,
          Days__ctx: {
            matchKey: '2023casj_qm1',
            alliance: ['frc254', 'frc604'],
            postResultTime: T,
            heldUntilPostResultTime: T + 86400,
          },
          Hours: 2,
          Hours__ctx: { postResultTime: T, heldUntilPostResultTime: T + 7200 },
          Minutes: 3,
          Minutes__ctx: { postResultTime: T, heldUntilPostResultTime: T + 60 },
          Seconds: 4,
          Seconds__ctx: { postResultTime: T, heldUntilPostResultTime: T - 5 },
          Current: 5,
          Current__ctx: { matchKey: '2023casj_qm2', postResultTime: T },
          Bare: 6,
          Bare__ctx: {},
        },
      },
    ];
    render(
      <TimeseriesInsight
        timeseries={timeseries({
          point_context_type: 'match_record',
          series: [...labels, 'Missing'].map((l) => recordSeries(l, [])),
        })}
      />,
    );
    expect(screen.getByTestId('x-axis').dataset.label).toBe('Date');
    expect(screen.getAllByTestId('line')[0].dataset.dot).toBe('true');
    const tooltip = screen.getByTestId('chart-tooltip');
    expect(tooltip.textContent).toBe(
      [
        'Nov 14, 2023',
        'Days: 1',
        'Set by 254, 604 in 2023casj_qm1',
        'Nov 14, 2023',
        'Held for 1 day',
        'Hours: 2',
        'Nov 14, 2023',
        'Held for 2 hours',
        'Minutes: 3',
        'Nov 14, 2023',
        'Held for 1 minute',
        'Seconds: 4',
        'Nov 14, 2023',
        'Held for 0 seconds',
        'Current: 5',
        'Nov 14, 2023',
        'Current record',
        'Bare: 6',
      ].join(''),
    );
  });

  test('omits the record tooltip when inactive or empty', () => {
    chart.tooltipActive = false;
    chart.tooltipPayload = [{ payload: { x: '2023', High: 1 } }];
    const { rerender } = render(
      <TimeseriesInsight timeseries={timeseries(recordData)} />,
    );
    expect(screen.getByTestId('chart-tooltip').textContent).toBe('');

    chart.tooltipActive = true;
    chart.tooltipPayload = [];
    rerender(<TimeseriesInsight timeseries={freshRecordTimeseries()} />);
    expect(screen.getByTestId('chart-tooltip').textContent).toBe('');

    chart.tooltipPayload = [{ payload: { x: '2023', High: 1 } }];
    rerender(<TimeseriesInsight timeseries={freshRecordTimeseries()} />);
    expect(screen.getByTestId('chart-tooltip').textContent).toBe('High: 1');
  });

  test('pins a record point on click and unpins it', () => {
    render(<TimeseriesInsight timeseries={timeseries(recordData)} />);

    click({ activeLabel: undefined, activeCoordinate: { x: 1, y: 2 } });
    click({ activeLabel: T });
    expect(screen.queryByRole('button', { name: 'Close' })).toBeNull();

    click({ activeLabel: T, activeCoordinate: { x: 10, y: 20 } });
    expect(screen.queryByTestId('chart-tooltip')).toBeNull();
    const close = screen.getByRole('button', { name: 'Close' });
    const overlay = close.parentElement?.parentElement;
    expect(overlay?.style.left).toBe('10px');
    expect(overlay?.style.top).toBe('20px');
    expect(overlay?.textContent).toContain('High: 100');
    expect(overlay?.textContent).toContain('Held for 2 days');

    fireEvent.click(close);
    expect(screen.queryByRole('button', { name: 'Close' })).toBeNull();
    expect(screen.getByTestId('chart-tooltip')).toBeTruthy();

    click({ activeLabel: T, activeCoordinate: { x: 10, y: 20 } });
    expect(screen.getByRole('button', { name: 'Close' })).toBeTruthy();
    click({ activeLabel: String(T), activeCoordinate: { x: 10, y: 20 } });
    expect(screen.queryByRole('button', { name: 'Close' })).toBeNull();

    // A pinned label with no matching row hides both the tooltip and overlay.
    click({ activeLabel: 1, activeCoordinate: { x: 1, y: 1 } });
    expect(screen.queryByTestId('chart-tooltip')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Close' })).toBeNull();
  });

  test('summarizes the current record', () => {
    render(<TimeseriesInsight timeseries={timeseries(recordData)} />);
    expect(screen.getByText(/Current record:/).textContent).toBe(
      'Current record: 2023casj_qm9',
    );
  });

  test('falls back to the latest record with its alliance', () => {
    render(
      <TimeseriesInsight
        timeseries={timeseries({
          point_context_type: 'match_record',
          series: [
            recordSeries('High', [
              { x: 2023, y: 1, context: { post_result_time: T } },
              {
                x: 2023,
                y: 2,
                context: {
                  match_key: '2023casj_qm1',
                  alliance: ['frc254', 'frc604'],
                  post_result_time: T + 1,
                },
              },
              {
                x: 2023,
                y: 3,
                context: {
                  match_key: '2023casj_qm2',
                  alliance: ['frc1', 'frc2'],
                  post_result_time: T + 2,
                },
              },
            ]),
          ],
        })}
      />,
    );
    expect(screen.getByText(/Latest:/).textContent).toBe(
      'Latest: 2023casj_qm2 (1, 2)',
    );
  });

  test('omits the summary without match records', () => {
    render(
      <TimeseriesInsight
        timeseries={timeseries({
          point_context_type: 'match_record',
          series: [
            recordSeries('High', [
              { x: 2023, y: 1 },
              { x: 2024, y: 1, context: { post_result_time: T } },
            ]),
          ],
        })}
      />,
    );
    expect(screen.queryByText(/Latest:|Current record:/)).toBeNull();
  });
});
