import { LoaderFunctionArgs } from '@remix-run/node';
import {
  ClientLoaderFunctionArgs,
  Link,
  MetaFunction,
  Params,
  json,
  useLoaderData,
} from '@remix-run/react';
import React from 'react';

import { LeaderboardInsight, getInsightsLeaderboardsYear } from '~/api/v3';
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
import { NAME_TO_DISPLAY_NAME } from '~/lib/insightUtils';
import { pluralize } from '~/lib/utils';

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

  const leaderboards = await getInsightsLeaderboardsYear({ year: numericYear });

  if (leaderboards.status !== 200) {
    throw new Response(null, {
      status: 500,
    });
  }

  if (leaderboards.data.length === 0) {
    throw new Response(null, {
      status: 404,
    });
  }

  return { year: numericYear, leaderboards: leaderboards.data };
}

export async function loader({ params }: LoaderFunctionArgs) {
  return json(await loadData(params));
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
  const { leaderboards, year } = useLoaderData<typeof loader>();

  return (
    <div>
      <SingleYearInsights leaderboards={leaderboards} year={year} />
    </div>
  );
}

function SingleYearInsights({
  year,
  leaderboards,
}: {
  year: number;
  leaderboards: LeaderboardInsight[];
}) {
  return (
    <div>
      <h1 className="mb-4 text-3xl font-bold">
        Insights ({year > 0 ? year : 'Overall'})
      </h1>

      <h3 className="mb-4 text-xl font-bold">Leaderboards</h3>
      <div className="lg:grid lg:grid-cols-2">
        {leaderboards.map((l, i) => (
          <Leaderboard leaderboard={l} key={i} />
        ))}
      </div>
    </div>
  );
}

const MAX_KEYS_PER_ROW = 20;
const PRE_EXPANDED_ROWS = 10;

function Leaderboard({ leaderboard }: { leaderboard: LeaderboardInsight }) {
  const [expanded, setExpanded] = React.useState(false);

  const displayName =
    NAME_TO_DISPLAY_NAME[leaderboard.name] || leaderboard.name;

  return (
    <div className="m-3">
      <Card>
        <CardHeader>
          <CardTitle>{displayName}</CardTitle>
          <CardDescription>
            {leaderboard.year > 0 ? leaderboard.year : 'Overall'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[6ch] text-center">#</TableHead>
                <TableHead className="text-left capitalize">
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
                      />
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>

          {leaderboard.data.rankings.length > PRE_EXPANDED_ROWS && (
            <Button
              variant="outline"
              className="w-full"
              onClick={() => {
                setExpanded((prev) => !prev);
              }}
            >
              {expanded ? 'Show Less' : 'Show More'}
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function LeaderboardKeyList({
  keyVals,
  keyType,
  cutoffSize,
}: {
  keyType: LeaderboardInsight['data']['key_type'];
  keyVals: string[];
  cutoffSize: number;
}) {
  return (
    <>
      {keyVals.slice(0, cutoffSize).map((k, i) => (
        <React.Fragment key={k}>
          {i > 0 && ', '}
          <LeaderboardKeyLink keyType={keyType} keyVal={k} />
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
    return (
      <Link to={`/team/${keyVal.substring(3)}`}>{keyVal.substring(3)}</Link>
    );
  }
  return <Link to={`/${keyType}/${keyVal}`}>{keyVal}</Link>;
}
