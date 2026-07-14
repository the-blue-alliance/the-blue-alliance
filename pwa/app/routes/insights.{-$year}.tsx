import { createFileRoute, notFound } from '@tanstack/react-router';

import {
  type InsightV2Leaderboard,
  type InsightV2Streak,
  type InsightV2Timeseries,
  getInsightsV2Year,
} from '~/api/tba/read';
import { Leaderboard } from '~/components/tba/leaderboard';
import { StreakInsight } from '~/components/tba/streakInsight';
import { TimeseriesInsight } from '~/components/tba/timeseriesInsight';
import { YearSelector } from '~/components/tba/yearSelector';
import { publicCacheControlHeaders, useValidYears } from '~/lib/utils';

export const Route = createFileRoute('/insights/{-$year}')({
  loader: async ({ params }) => {
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

    const insights = await getInsightsV2Year({
      path: { year: numericYear },
    });

    if (insights.data === undefined) {
      throw new Error('Failed to load insights');
    }

    if (insights.data.length === 0) {
      throw notFound();
    }

    const leaderboards: InsightV2Leaderboard[] = [];
    const streaks: InsightV2Streak[] = [];
    const timeseries: InsightV2Timeseries[] = [];

    for (const insight of insights.data) {
      switch (insight.category) {
        case 'leaderboard':
          leaderboards.push(insight);
          break;
        case 'streak':
          streaks.push(insight);
          break;
        case 'timeseries':
          timeseries.push(insight);
          break;
      }
    }

    return {
      year: numericYear,
      leaderboards,
      streaks,
      timeseries,
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

function InsightsPage() {
  const { leaderboards, streaks, timeseries, year } = Route.useLoaderData();

  return (
    <div>
      <SingleYearInsights
        leaderboards={leaderboards}
        streaks={streaks}
        timeseries={timeseries}
        year={year}
      />
    </div>
  );
}

function SectionHeading({ children }: { children: string }) {
  return (
    <h2 className="mb-4 flex items-center gap-2 text-2xl font-semibold">
      <span
        className="inline-block h-1 w-8 rounded-full bg-gradient-to-r
          from-primary to-primary/50"
      />
      {children}
    </h2>
  );
}

function SingleYearInsights({
  year,
  leaderboards,
  streaks,
  timeseries,
}: {
  year: number;
  leaderboards: InsightV2Leaderboard[];
  streaks: InsightV2Streak[];
  timeseries: InsightV2Timeseries[];
}) {
  const validYears = useValidYears();

  return (
    <div className="py-8">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1
            className="bg-gradient-to-r from-foreground to-foreground/70
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

      {leaderboards.length > 0 && (
        <div className="mb-8">
          <SectionHeading>Leaderboards</SectionHeading>
          <div className="grid gap-6 lg:grid-cols-2">
            {leaderboards.map((l) => (
              <Leaderboard
                subtitle={l.year > 0 ? `${l.year}` : 'Overall'}
                leaderboard={l}
                displayName={l.display_name}
                key={l.name}
                year={year}
              />
            ))}
          </div>
        </div>
      )}

      {streaks.length > 0 && (
        <div className="mb-8">
          <SectionHeading>Streaks</SectionHeading>
          <div className="grid gap-6 lg:grid-cols-2">
            {streaks.map((s) => (
              <StreakInsight
                subtitle={s.year > 0 ? `${s.year}` : 'Overall'}
                streak={s}
                key={s.name}
              />
            ))}
          </div>
        </div>
      )}

      {timeseries.length > 0 && (
        <div>
          <SectionHeading>Timeseries</SectionHeading>
          <div className="grid gap-6 lg:grid-cols-2">
            {timeseries.map((t) => (
              <TimeseriesInsight
                subtitle={t.year > 0 ? `${t.year}` : 'Overall'}
                timeseries={t}
                key={t.name}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
