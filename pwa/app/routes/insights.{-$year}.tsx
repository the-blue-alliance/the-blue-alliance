import { useSuspenseQueries } from '@tanstack/react-query';
import { createFileRoute, notFound } from '@tanstack/react-router';

import { type Event, type InsightV2Leaderboard } from '~/api/tba/read';
import {
  getEventsByYearOptions,
  getInsightsV2YearOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { InsightSections } from '~/components/tba/insightSections';
import { YearSelector } from '~/components/tba/yearSelector';
import {
  type GroupedInsights,
  groupInsightsByCategory,
} from '~/lib/insightUtils';
import { parseMatchKey } from '~/lib/matchUtils';
import { STALE_TIME, staleTimeForYear } from '~/lib/queryClient';
import { publicCacheControlHeaders, useValidYears } from '~/lib/utils';

export const Route = createFileRoute('/insights/{-$year}')({
  loader: async ({ params, context: { queryClient } }) => {
    let numericYear = -1;
    if (params.year === undefined || params.year === '') {
      numericYear = 0;
    } else {
      const parsed = Number(params.year);
      if (!Number.isNaN(parsed) && parsed > 0) {
        numericYear = parsed;
      }
    }

    if (numericYear === -1) {
      throw notFound();
    }

    const insights = await queryClient.ensureQueryData({
      ...getInsightsV2YearOptions({ path: { year: numericYear } }),
      staleTime:
        numericYear === 0 ? STALE_TIME.DEFAULT : staleTimeForYear(numericYear),
    });

    if (insights.length === 0) {
      throw notFound();
    }

    const { leaderboards, streaks, timeseries, successRates } =
      groupInsightsByCategory(insights);

    // Event and match leaderboards render names, not keys, which needs the
    // events behind those keys. Overall (year 0) boards can span seasons.
    const eventYears = leaderboardEventYears(leaderboards);
    await Promise.all(
      eventYears.map((eventYear) =>
        queryClient.ensureQueryData({
          ...getEventsByYearOptions({ path: { year: eventYear } }),
          staleTime: staleTimeForYear(eventYear),
        }),
      ),
    );
    return {
      year: numericYear,
      eventYears,
      leaderboards,
      streaks,
      timeseries,
      successRates,
    };
  },
  headers: publicCacheControlHeaders(),
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [
          { title: 'Insights - The Blue Alliance' },
          {
            name: 'description',
            content: 'Insights for the FIRST Robotics Competition.',
          },
        ],
      };
    }

    return {
      meta: [
        {
          title: `${loaderData.year > 0 ? loaderData.year : 'Overall'} Insights - The Blue Alliance`,
        },
        {
          name: 'description',
          content: `${loaderData.year > 0 ? loaderData.year : 'Overall'} insights for the FIRST Robotics Competition.`,
        },
      ],
    };
  },
  component: InsightsPage,
});

/** Seasons whose events are referenced by event or match keys in the boards. */
function leaderboardEventYears(leaderboards: InsightV2Leaderboard[]): number[] {
  const years = new Set<number>();
  for (const board of leaderboards) {
    const keyType = board.data.key_type;
    if (keyType !== 'event' && keyType !== 'match') {
      continue;
    }
    for (const ranking of board.data.rankings) {
      for (const key of ranking.keys) {
        if (typeof key !== 'string') {
          continue;
        }
        const eventKey =
          keyType === 'match' ? parseMatchKey(key)?.eventKey : key;
        const year = Number(eventKey?.slice(0, 4));
        if (year > 0) {
          years.add(year);
        }
      }
    }
  }
  return [...years].sort((a, b) => a - b);
} // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop

function InsightsPage() {
  const { leaderboards, streaks, timeseries, successRates, year, eventYears } =
    Route.useLoaderData();
  const eventQueries = useSuspenseQueries({
    queries: eventYears.map((eventYear) => ({
      ...getEventsByYearOptions({ path: { year: eventYear } }),
      staleTime: staleTimeForYear(eventYear),
    })),
  });
  const eventsByKey = new Map<string, Event>();
  for (const query of eventQueries) {
    for (const event of query.data) {
      eventsByKey.set(event.key, event);
    }
  }

  return (
    <div>
      <SingleYearInsights
        eventsByKey={eventsByKey}
        leaderboards={leaderboards}
        streaks={streaks}
        timeseries={timeseries}
        successRates={successRates}
        year={year}
      />
    </div>
  );
}

function SingleYearInsights({
  year,
  eventsByKey,
  ...insights
}: GroupedInsights & {
  year: number;
  eventsByKey: ReadonlyMap<string, Event>;
}) {
  const validYears = useValidYears();

  return (
    <div className="py-8">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1
            className="bg-linear-to-r from-foreground to-foreground/70
              bg-clip-text text-4xl font-bold tracking-tight text-transparent"
          >
            Insights
          </h1>
          <p className="mt-2 text-lg text-muted-foreground">
            {year > 0 ? `${year} Season` : 'All-Time Records'}
          </p>
        </div>

        <YearSelector
          currentLabel={year > 0 ? String(year) : 'Overall'}
          triggerClassName="w-[180px] border-border/50 shadow-sm"
          options={[
            {
              label: 'Overall',
              to: '/insights',
              isCurrent: year === 0,
            },
            ...validYears.map((y) => ({
              label: String(y),
              to: `/insights/${y}`,
              isCurrent: y === year,
            })),
          ]}
        />
      </div>

      <InsightSections year={year} eventsByKey={eventsByKey} {...insights} />
    </div>
  );
}
