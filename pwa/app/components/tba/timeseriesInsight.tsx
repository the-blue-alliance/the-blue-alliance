import { useMemo, useState } from 'react';
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from 'recharts';
import { Temporal } from 'temporal-polyfill';

import MaterialSymbolsCloseRounded from '~icons/material-symbols/close-rounded';

import { type InsightV2Timeseries } from '~/api/tba/read';
import { MatchLink, TeamLink } from '~/components/tba/links';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from '~/components/ui/chart';
import {
  type ChartRow,
  type RecordContext,
  contextKey,
  mergeSeries,
  timeseriesHasTemporalXAxis,
} from '~/lib/insightUtils';
import { pluralize } from '~/lib/utils';

const CHART_COLORS = [
  'var(--color-brand)',
  'var(--color-chart-2)',
  'var(--color-chart-3)',
  'var(--color-chart-4)',
  'var(--color-chart-5)',
];

type TimeseriesSeries = InsightV2Timeseries['data']['series'];

function formatEpochSeconds(epochSeconds: number): string {
  if (!Number.isFinite(epochSeconds)) {
    return '';
  }
  return Temporal.Instant.fromEpochMilliseconds(Math.round(epochSeconds) * 1000)
    .toZonedDateTimeISO('UTC')
    .toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
}

/**
 * Formats the duration a record stood for, given the epoch seconds it was
 * set and (if since overtaken) the epoch seconds of the record that broke
 * it. Still-standing records report as such rather than a duration to "now".
 */
function formatHeldDuration(
  postResultTime: number,
  heldUntilPostResultTime: number | undefined,
): string {
  if (heldUntilPostResultTime === undefined) {
    return 'Current record';
  }
  const heldSeconds = Math.max(
    0,
    Math.floor(heldUntilPostResultTime - postResultTime),
  );

  const days = Math.floor(heldSeconds / 86400);
  if (days >= 1) {
    return `Held for ${pluralize(days, 'day', 'days')}`;
  }
  const hours = Math.floor(heldSeconds / 3600);
  if (hours >= 1) {
    return `Held for ${pluralize(hours, 'hour', 'hours')}`;
  }
  const minutes = Math.floor(heldSeconds / 60);
  if (minutes >= 1) {
    return `Held for ${pluralize(minutes, 'minute', 'minutes')}`;
  }
  return `Held for ${pluralize(heldSeconds, 'second', 'seconds')}`;
}

interface PinnedPoint {
  x: string | number;
  coordinate: { x: number; y: number };
}

export function TimeseriesInsight({
  timeseries,
  subtitle,
}: {
  timeseries: InsightV2Timeseries;
  subtitle?: string;
}) {
  const usePostResultTime =
    timeseries.data.point_context_type === 'match_record';
  const temporalXAxis = timeseriesHasTemporalXAxis(timeseries.data);

  const rows = useMemo(() => mergeSeries(timeseries.data), [timeseries.data]);

  const [pinned, setPinned] = useState<PinnedPoint | null>(null);

  const pinnedRow = useMemo(
    () =>
      pinned ? rows.find((r) => String(r.x) === String(pinned.x)) : undefined,
    [pinned, rows],
  );

  const chartConfig = useMemo(() => {
    const config: ChartConfig = {};
    timeseries.data.series.forEach((series, i) => {
      config[series.label] = {
        label: series.label,
        color: CHART_COLORS[i % CHART_COLORS.length],
      };
    });
    return config;
  }, [timeseries.data.series]);

  return (
    <Card
      className="overflow-hidden border-border/50 shadow-sm transition-shadow
        hover:shadow-md"
    >
      <CardHeader
        className="border-b bg-linear-to-br from-muted/30 to-muted/10 px-6 pt-5
          pb-4"
      >
        <CardTitle className="text-lg leading-tight font-semibold">
          {timeseries.display_name}
        </CardTitle>
        {subtitle && (
          <CardDescription className="mt-0.5 text-sm">
            {subtitle}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="p-4">
        <div className="relative">
          <ChartContainer config={chartConfig} className="min-h-[250px] w-full">
            <LineChart
              accessibilityLayer
              data={rows}
              margin={{ top: 5, right: 5, bottom: 5, left: -8 }}
              onClick={(state) => {
                if (!usePostResultTime) {
                  return;
                }
                const { activeLabel, activeCoordinate } = state;
                if (activeLabel === undefined || !activeCoordinate) {
                  return;
                }
                setPinned((prev) =>
                  prev && String(prev.x) === String(activeLabel)
                    ? null
                    : { x: activeLabel, coordinate: activeCoordinate },
                );
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="x"
                type={temporalXAxis ? 'number' : 'category'}
                domain={temporalXAxis ? ['dataMin', 'dataMax'] : undefined}
                tickFormatter={
                  temporalXAxis
                    ? (x: number) => formatEpochSeconds(x)
                    : undefined
                }
                label={{
                  value: usePostResultTime ? 'Date' : timeseries.data.x_label,
                  position: 'bottom',
                }}
              />
              <YAxis
                label={{
                  value: timeseries.data.y_label,
                  angle: -90,
                  position: 'insideLeft',
                  dx: 8,
                  style: { textAnchor: 'middle' },
                }}
              />
              {timeseries.data.series.map((series, i) => (
                <Line
                  key={series.label}
                  dataKey={series.label}
                  stroke={CHART_COLORS[i % CHART_COLORS.length]}
                  dot={usePostResultTime}
                  strokeWidth={2}
                  type="monotone"
                  connectNulls
                />
              ))}
              {!pinned && (
                <ChartTooltip
                  content={
                    usePostResultTime ? (
                      <RecordTooltipContent series={timeseries.data.series} />
                    ) : temporalXAxis ? (
                      <ChartTooltipContent
                        labelFormatter={(_, payload) =>
                          formatEpochSeconds(
                            Number(payload?.[0]?.payload?.x ?? NaN),
                          )
                        }
                      />
                    ) : (
                      <ChartTooltipContent />
                    )
                  }
                />
              )}
            </LineChart>
          </ChartContainer>
          {pinned && pinnedRow && (
            <div
              className="pointer-events-none absolute z-10"
              style={{
                left: pinned.coordinate.x,
                top: pinned.coordinate.y,
                transform: 'translate(-50%, calc(-100% - 12px))',
              }}
            >
              <div className="pointer-events-auto relative">
                <button
                  type="button"
                  onClick={() => setPinned(null)}
                  className="absolute -top-2 -right-2 flex h-5 w-5 items-center
                    justify-center rounded-full border bg-background
                    text-muted-foreground shadow-sm hover:text-foreground"
                  aria-label="Close"
                >
                  <MaterialSymbolsCloseRounded className="h-3 w-3" />
                </button>
                <RecordTooltipBody
                  row={pinnedRow}
                  series={timeseries.data.series}
                />
              </div>
            </div>
          )}
        </div>
        {timeseries.data.point_context_type === 'match_record' && (
          <MatchRecordTable timeseries={timeseries} />
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Renders who set a record, when, and how long they held it for a single
 * chart row. Shared between the hover-triggered tooltip and the frozen
 * overlay shown after a click, so clicking the match link inside stays
 * possible (a hover tooltip vanishes as soon as the mouse leaves it).
 */
function RecordTooltipBody({
  row,
  series,
}: {
  row: ChartRow;
  series: TimeseriesSeries;
}) {
  return (
    <div
      className="grid min-w-[220px] gap-2 rounded-lg border bg-background px-3
        py-2 text-xs shadow-md"
    >
      {typeof row.x === 'number' && (
        <div className="font-medium text-foreground">
          {formatEpochSeconds(row.x)}
        </div>
      )}
      {series.map((s, i) => {
        const value = row[s.label] as number | undefined;
        if (value === undefined) {
          return null;
        }
        const context = row[contextKey(s.label)] as RecordContext | undefined;

        return (
          <div key={s.label} className="flex flex-col gap-0.5">
            <div className="flex items-center gap-1.5">
              <span
                className="h-2 w-2 shrink-0 rounded-[2px]"
                style={{
                  backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
                }}
              />
              <span className="font-medium text-foreground">
                {s.label}: {value}
              </span>
            </div>
            {context && (
              <div className="pl-3.5 text-muted-foreground">
                {context.matchKey && context.alliance && (
                  <div>
                    Set by{' '}
                    {context.alliance.map((teamKey, j) => (
                      <span key={teamKey}>
                        {j > 0 && ', '}
                        <TeamLink teamOrKey={teamKey} year={0}>
                          {teamKey.substring(3)}
                        </TeamLink>
                      </span>
                    ))}{' '}
                    in{' '}
                    <MatchLink matchOrKey={context.matchKey}>
                      {context.matchKey}
                    </MatchLink>
                  </div>
                )}
                {context.postResultTime !== undefined && (
                  <div>{formatEpochSeconds(context.postResultTime)}</div>
                )}
                {context.postResultTime !== undefined && (
                  <div>
                    {formatHeldDuration(
                      context.postResultTime,
                      context.heldUntilPostResultTime,
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/**
 * Hover-triggered tooltip content, used while no point is pinned.
 */
function RecordTooltipContent({
  active,
  payload,
  series,
}: {
  active?: boolean;
  payload?: Array<{ payload?: ChartRow }>;
  series?: TimeseriesSeries;
}) {
  const row = payload?.[0]?.payload;
  if (!active || !row || !series) {
    return null;
  }

  return <RecordTooltipBody row={row} series={series} />;
}

function MatchRecordTable({ timeseries }: { timeseries: InsightV2Timeseries }) {
  const records = timeseries.data.series.flatMap((series) =>
    series.points
      .filter((p) => p.context?.match_key)
      .map((p) => ({ series: series.label, point: p })),
  );

  if (records.length === 0) {
    return null;
  }

  const current = records.filter((r) => r.point.context?.is_current);
  const toShow = current.length > 0 ? current : records.slice(-1);

  return (
    <div className="mt-4 flex flex-wrap gap-2 text-sm text-muted-foreground">
      {toShow.map(({ series, point }) => (
        <span key={`${series}-${point.context?.match_key}`}>
          {point.context?.is_current ? 'Current record: ' : 'Latest: '}
          {point.context?.match_key && (
            <MatchLink matchOrKey={point.context.match_key}>
              {point.context.match_key}
            </MatchLink>
          )}
          {point.context?.alliance && point.context.alliance.length > 0 && (
            <>
              {' '}
              (
              {point.context.alliance.map((teamKey, i) => (
                <span key={teamKey}>
                  {i > 0 && ', '}
                  <TeamLink teamOrKey={teamKey} year={0}>
                    {teamKey.substring(3)}
                  </TeamLink>
                </span>
              ))}
              )
            </>
          )}
        </span>
      ))}
    </div>
  );
}
