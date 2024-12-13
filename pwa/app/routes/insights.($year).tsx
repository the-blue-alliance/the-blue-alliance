import { LoaderFunctionArgs } from '@remix-run/node';
import {
  ClientLoaderFunctionArgs,
  Link,
  MetaFunction,
  Params,
  useLoaderData,
} from '@remix-run/react';
import React, { ReactNode } from 'react';

import BiChevronBarDown from '~icons/bi/chevron-bar-down';
import BiChevronBarUp from '~icons/bi/chevron-bar-up';

import {
  LeaderboardInsight,
  NotablesInsight,
  getInsightsLeaderboardsYear,
  getInsightsNotablesYear,
} from '~/api/v3';
import { TitledCard } from '~/components/tba/cards';
import { EventLink, TeamLink } from '~/components/tba/links';
import { Button } from '~/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import {
  LEADERBOARD_NAME_TO_DISPLAY_NAME,
  NOTABLE_NAME_TO_DISPLAY_NAME,
  leaderboardFromNotable,
} from '~/lib/insightUtils';
import { joinComponents, pluralize } from '~/lib/utils';

async function loadData(params: Params) {
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

export async function loader({ params }: LoaderFunctionArgs) {
  return await loadData(params);
}

export async function clientLoader({ params }: ClientLoaderFunctionArgs) {
  return await loadData(params);
}

export const meta: MetaFunction<typeof loader> = ({ data }) => {
  return [
    {
      title: `${(data?.year ?? 0) > 0 ? data?.year : 'Overall'} Insights - The Blue Alliance`,
    },
    {
      name: 'description',
      content: `${(data?.year ?? 0) > 0 ? data?.year : 'Overall'} insights for the FIRST Robotics Competition.`,
    },
  ];
};

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
          <Leaderboard leaderboard={l} key={i} />
        ))}
      </div>
    </div>
  );
}

const MAX_KEYS_PER_ROW = 20;
const PRE_EXPANDED_ROWS = 10;

function Leaderboard({
  leaderboard,
  contextTooltipMap,
}: {
  leaderboard: LeaderboardInsight;
  contextTooltipMap?: Record<string, ReactNode>;
}) {
  const [expanded, setExpanded] = React.useState(false);

  const displayName =
    LEADERBOARD_NAME_TO_DISPLAY_NAME[leaderboard.name] || leaderboard.name;

  return (
    <Card className="border-gray-300">
      <CardHeader className="px-6 pb-1 pt-4">
        <CardTitle>
          <div className="flex justify-between align-middle">
            <div className="self-center">{displayName}</div>
            <Button
              variant={'ghost'}
              onClick={() => {
                setExpanded(!expanded);
              }}
              size={'sm'}
            >
              {expanded ? <BiChevronBarUp /> : <BiChevronBarDown />}
              <span className="sr-only">Toggle</span>
            </Button>
          </div>
        </CardTitle>
        <CardDescription>
          {leaderboard.year > 0 ? leaderboard.year : 'Overall'}
        </CardDescription>
      </CardHeader>
      <CardContent className="pb-3">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="h-8 w-[6ch] text-center">#</TableHead>
              <TableHead className="h-8 text-left capitalize">
                {leaderboard.data.key_type}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {leaderboard.data.rankings
              .slice(0, expanded ? 100 : PRE_EXPANDED_ROWS)
              .map((r, i) => (
                <TableRow key={i}>
                  <TableCell className="text-center">{r.value}</TableCell>
                  <TableCell className="pl-4 text-left">
                    <LeaderboardKeyList
                      cutoffSize={MAX_KEYS_PER_ROW}
                      keyType={leaderboard.data.key_type}
                      keyVals={r.keys}
                      contextTooltipMap={contextTooltipMap}
                    />
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function LeaderboardKeyList({
  keyVals,
  keyType,
  cutoffSize,
  contextTooltipMap,
}: {
  keyType: LeaderboardInsight['data']['key_type'];
  keyVals: string[];
  cutoffSize: number;
  contextTooltipMap?: Record<string, ReactNode>;
}) {
  return (
    <>
      {keyVals.slice(0, cutoffSize).map((k, i) => (
        <React.Fragment key={k}>
          {i > 0 && ', '}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <LeaderboardKeyLink keyType={keyType} keyVal={k} />
              </TooltipTrigger>
              <TooltipContent>
                {contextTooltipMap?.[k] ? <p>{contextTooltipMap[k]}</p> : null}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </React.Fragment>
      ))}
      {keyVals.length > cutoffSize && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger className="italic">
              &nbsp;(and{' '}
              {pluralize(keyVals.length - cutoffSize, 'other', 'others')})
            </TooltipTrigger>
            <TooltipContent className="max-w-[500px] whitespace-normal break-words text-center">
              <p>
                {keyVals.map((k, i) => (
                  <React.Fragment key={k}>
                    {i > 0 && ', '}
                    <LeaderboardKeyLink keyType={keyType} keyVal={k} />
                  </React.Fragment>
                ))}
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </>
  );
}

function LeaderboardKeyLink({
  keyVal,
  keyType,
}: {
  keyType: LeaderboardInsight['data']['key_type'];
  keyVal: string;
}) {
  if (keyType === 'team') {
    return <TeamLink teamOrKey={keyVal}>{keyVal.substring(3)}</TeamLink>;
  }
  return <Link to={`/${keyType}/${keyVal}`}>{keyVal}</Link>;
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
            '-',
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
            '-',
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

function NotablesOverall({ notables }: { notables: NotablesInsight[] }) {
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
          />
        );
      })}
    </div>
  );
}
