import { ReactNode } from 'react';
import { useLoaderData } from 'react-router';

import {
  LeaderboardInsight,
  NotablesInsight,
  getInsightsLeaderboardsYear,
  getInsightsNotablesYear,
} from '~/api/v3';
import { TitledCard } from '~/components/tba/cards';
import { Leaderboard } from '~/components/tba/leaderboard';
import { EventLink, TeamLink } from '~/components/tba/links';
import {
  NOTABLE_NAME_TO_DISPLAY_NAME,
  leaderboardFromNotable,
} from '~/lib/insightUtils';
import { joinComponents } from '~/lib/utils';

import { Route } from '.react-router/types/app/routes/+types/insights.($year)';

async function loadData(params: Route.LoaderArgs['params']) {
  let numericYear = -1;
  if (params.year === undefined) {
    numericYear = 0;
  } else {
    const parsed = Number(params.year);
    if (!Number.isNaN(parsed) && parsed > 0) {
      numericYear = parsed;
    }
  }

  if (numericYear === -1) {
    throw new Response(null, {
      status: 404,
    });
  }

  const [leaderboards, notables] = await Promise.all([
    getInsightsLeaderboardsYear({ year: numericYear }),
    getInsightsNotablesYear({ year: numericYear }),
  ]);

  if (leaderboards.status !== 200 || notables.status !== 200) {
    throw new Response(null, {
      status: 500,
    });
  }

  if (leaderboards.data.length === 0 || notables.data.length === 0) {
    throw new Response(null, {
      status: 404,
    });
  }

  return {
    year: numericYear,
    leaderboards: leaderboards.data,
    notables: notables.data,
  };
}

export async function loader({ params }: Route.LoaderArgs) {
  return await loadData(params);
}

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return await loadData(params);
}

export function meta({ data }: Route.MetaArgs) {
  return [
    {
      title: `${data.year > 0 ? data.year : 'Overall'} Insights - The Blue Alliance`,
    },
    {
      name: 'description',
      content: `${data.year > 0 ? data.year : 'Overall'} insights for the FIRST Robotics Competition.`,
    },
  ];
}

export default function InsightsPage() {
  const { leaderboards, year, notables } = useLoaderData<typeof loader>();

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
      <h1 className="mb-3 text-3xl font-medium">
        Insights ({year > 0 ? year : 'Overall'})
      </h1>

      <h3 className="mb-4 text-xl font-medium">Notables</h3>
      {notableDiv}

      <h3 className="my-4 text-xl font-medium">Leaderboards</h3>
      <div className="gap-3 lg:grid lg:grid-cols-2">
        {leaderboards.map((l, i) => (
          <Leaderboard leaderboard={l} key={i} year={year} />
        ))}
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
    <div className="gap-3 lg:grid lg:grid-cols-2">
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
    <div className="gap-3 lg:grid lg:grid-cols-2">
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
