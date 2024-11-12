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

import BiChevronBarDown from '~icons/bi/chevron-bar-down';
import BiChevronBarUp from '~icons/bi/chevron-bar-up';

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
    <div className="py-8">
      <h1 className="mb-3 text-3xl font-medium">
        Insights ({year > 0 ? year : 'Overall'})
      </h1>

      <h3 className="mb-4 text-xl font-medium">Leaderboards</h3>
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

function Leaderboard({ leaderboard }: { leaderboard: LeaderboardInsight }) {
  const [expanded, setExpanded] = React.useState(false);

  const displayName =
    NAME_TO_DISPLAY_NAME[leaderboard.name] || leaderboard.name;

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
