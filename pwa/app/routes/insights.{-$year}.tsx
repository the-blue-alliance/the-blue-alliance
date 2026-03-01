import { createFileRoute, notFound, useNavigate } from '@tanstack/react-router';
import { ReactNode } from 'react';

import {
  LeaderboardInsight,
  NotablesInsight,
  getInsightsLeaderboardsYear,
  getInsightsNotablesYear,
} from '~/api/tba/read';
import { TitledCard } from '~/components/tba/cards';
import { Leaderboard } from '~/components/tba/leaderboard';
import { EventLink, TeamLink } from '~/components/tba/links';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import {
  NOTABLE_NAME_TO_DISPLAY_NAME,
  leaderboardFromNotable,
} from '~/lib/insightUtils';
import {
  joinComponents,
  publicCacheControlHeaders,
  useValidYears,
} from '~/lib/utils';

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

    const [leaderboards, notables] = await Promise.all([
      getInsightsLeaderboardsYear({ path: { year: numericYear } }),
      getInsightsNotablesYear({ path: { year: numericYear } }),
    ]);

    if (leaderboards.data === undefined || notables.data === undefined) {
      throw new Error('Failed to load insights');
    }

    if (leaderboards.data.length === 0 || notables.data.length === 0) {
      throw notFound();
    }

    return {
      year: numericYear,
      leaderboards: leaderboards.data,
      notables: notables.data,
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
  const { leaderboards, year, notables } = Route.useLoaderData();

  return (
    <div>
      <SingleYearInsights
        leaderboards={leaderboards}
        year={year}
        notables={notables}
      />
    </div>
  );
}

function SingleYearInsights({
  year,
  leaderboards,
  notables,
}: {
  year: number;
  leaderboards: LeaderboardInsight[];
  notables: NotablesInsight[];
}) {
  const validYears = useValidYears();
  const navigate = useNavigate();

  const notableDiv =
    year !== 0 ? (
      <NotablesYearSpecific notables={notables} />
    ) : (
      <NotablesOverall
        notables={notables.filter((n) => n.name !== 'notables_hall_of_fame')}
        year={0}
      />
    );

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

        <Select
          value={year > 0 ? `${year}` : 'Overall'}
          onValueChange={(value) => {
            void navigate({
              to: '/insights/{-$year}',
              params: { year: value === 'Overall' ? '' : value },
            });
          }}
        >
          <SelectTrigger
            className="w-[180px] cursor-pointer border-border/50 shadow-sm"
          >
            <SelectValue placeholder="Overall" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Overall" className="cursor-pointer">
              Overall
            </SelectItem>
            {validYears.map((y) => (
              <SelectItem key={y} value={`${y}`} className="cursor-pointer">
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="mb-8">
        <h2 className="mb-4 flex items-center gap-2 text-2xl font-semibold">
          <span
            className="inline-block h-1 w-8 rounded-full bg-gradient-to-r
              from-primary to-primary/50"
          />
          Notables
        </h2>
        {notableDiv}
      </div>

      <div>
        <h2 className="mb-4 flex items-center gap-2 text-2xl font-semibold">
          <span
            className="inline-block h-1 w-8 rounded-full bg-gradient-to-r
              from-primary to-primary/50"
          />
          Leaderboards
        </h2>
        <div className="grid gap-6 lg:grid-cols-2">
          {leaderboards.map((l, i) => (
            <Leaderboard leaderboard={l} key={i} year={year} />
          ))}
        </div>
      </div>
    </div>
  );
}

function NotablesYearSpecific({ notables }: { notables: NotablesInsight[] }) {
  const hof = notables.find((n) => n.name === 'notables_hall_of_fame');
  const worldChamps = notables.find(
    (n) => n.name === 'notables_world_champions',
  );

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {hof && (
        <TitledCard
          cardTitle={joinComponents(
            hof.data.entries.map((e) => (
              <TeamLink key={e.team_key} teamOrKey={e.team_key} year={hof.year}>
                {e.team_key.substring(3)}
              </TeamLink>
            )),
            <span className="font-medium">, </span>,
          )}
          cardSubtitle={
            <>
              {NOTABLE_NAME_TO_DISPLAY_NAME[hof.name] || hof.name} {hof.year}
            </>
          }
        />
      )}
      {worldChamps && (
        <TitledCard
          cardTitle={joinComponents(
            worldChamps.data.entries.map((e) => (
              <TeamLink
                key={e.team_key}
                teamOrKey={e.team_key}
                year={worldChamps.year}
              >
                {e.team_key.substring(3)}
              </TeamLink>
            )),
            <span className="font-medium">, </span>,
          )}
          cardSubtitle={
            <>
              {NOTABLE_NAME_TO_DISPLAY_NAME[worldChamps.name] ||
                worldChamps.name}{' '}
              {worldChamps.year}
            </>
          }
        />
      )}
    </div>
  );
}

function NotablesOverall({
  notables,
  year,
}: {
  notables: NotablesInsight[];
  year: number;
}) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {notables.map((n, i) => {
        const leaderboard = leaderboardFromNotable(n);
        const context = n.data.entries.reduce<Record<string, ReactNode>>(
          (acc, entry) => {
            acc[entry.team_key] = joinComponents(
              entry.context.map((c, i) => (
                <EventLink eventOrKey={c} key={i}>
                  {c}
                </EventLink>
              )),
              ', ',
            );
            return acc;
          },
          {},
        );

        return (
          <Leaderboard
            leaderboard={leaderboard}
            key={i}
            contextTooltipMap={context}
            year={year}
          />
        );
      })}
    </div>
  );
}
