import React, { ReactNode } from 'react';
import { Link } from 'react-router';

import BiChevronBarDown from '~icons/bi/chevron-bar-down';
import BiChevronBarUp from '~icons/bi/chevron-bar-up';

import { LeaderboardInsight } from '~/api/tba';
import { TeamLink } from '~/components/tba/links';
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
import { LEADERBOARD_NAME_TO_DISPLAY_NAME } from '~/lib/insightUtils';
import { pluralize } from '~/lib/utils';

const MAX_KEYS_PER_ROW = 20;
const PRE_EXPANDED_ROWS = 10;

export function Leaderboard({
  leaderboard,
  contextTooltipMap,
  year,
}: {
  leaderboard: LeaderboardInsight;
  contextTooltipMap?: Record<string, ReactNode>;
  year: number;
}) {
  const [expanded, setExpanded] = React.useState(false);

  const displayName =
    LEADERBOARD_NAME_TO_DISPLAY_NAME[leaderboard.name] || leaderboard.name;

  return (
    <Card className="border-gray-300">
      <CardHeader className="px-6 pt-4 pb-1">
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
                      year={year}
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
  year,
}: {
  keyType: LeaderboardInsight['data']['key_type'];
  keyVals: string[];
  cutoffSize: number;
  contextTooltipMap?: Record<string, ReactNode>;
  year: number;
}) {
  return (
    <>
      {keyVals.slice(0, cutoffSize).map((k, i) => (
        <React.Fragment key={k}>
          {i > 0 && ', '}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <LeaderboardKeyLink keyType={keyType} keyVal={k} year={year} />
              </TooltipTrigger>
              {contextTooltipMap?.[k] ? (
                <TooltipContent>
                  <p>{contextTooltipMap[k]}</p>
                </TooltipContent>
              ) : null}
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
            <TooltipContent className="max-w-[500px] text-center break-words whitespace-normal">
              <p>
                {keyVals.map((k, i) => (
                  <React.Fragment key={k}>
                    {i > 0 && ', '}
                    <LeaderboardKeyLink
                      keyType={keyType}
                      keyVal={k}
                      year={year}
                    />
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
  year,
}: {
  keyType: LeaderboardInsight['data']['key_type'];
  keyVal: string;
  year: number;
}) {
  if (keyType === 'team') {
    return (
      <TeamLink teamOrKey={keyVal} year={year}>
        {keyVal.substring(3)}
      </TeamLink>
    );
  }
  return <Link to={`/${keyType}/${keyVal}`}>{keyVal}</Link>;
}
