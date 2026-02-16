import { Link } from '@tanstack/react-router';
import { Fragment, type ReactNode, useState } from 'react';

import BiChevronBarDown from '~icons/bi/chevron-bar-down';
import BiChevronBarUp from '~icons/bi/chevron-bar-up';
import MaterialSymbolsTrophy from '~icons/material-symbols/trophy';

import { LeaderboardInsight } from '~/api/tba/read';
import { MatchLink, TeamLink } from '~/components/tba/links';
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
import { cn, pluralize } from '~/lib/utils';

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
  const [expanded, setExpanded] = useState(false);

  const displayName =
    LEADERBOARD_NAME_TO_DISPLAY_NAME[leaderboard.name] || leaderboard.name;

  return (
    <Card
      className="overflow-hidden border-border/50 shadow-sm transition-shadow
        hover:shadow-md"
    >
      <CardHeader
        className="border-b bg-gradient-to-br from-muted/30 to-muted/10 px-6
          pt-5 pb-4"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg
                bg-primary/10"
            >
              <MaterialSymbolsTrophy className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg leading-tight font-semibold">
                {displayName}
              </CardTitle>
              <CardDescription className="mt-0.5 text-sm">
                {leaderboard.year > 0 ? leaderboard.year : 'Overall'}
              </CardDescription>
            </div>
          </div>
          <Button
            variant="ghost"
            onClick={() => {
              setExpanded(!expanded);
            }}
            size="sm"
            className="h-9 w-9 p-0 hover:bg-primary/10"
          >
            {expanded ? (
              <BiChevronBarUp className="h-4 w-4" />
            ) : (
              <BiChevronBarDown className="h-4 w-4" />
            )}
            <span className="sr-only">Toggle</span>
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="h-10 w-[4.5rem] text-center font-semibold">
                Count
              </TableHead>
              <TableHead className="h-10 text-left font-semibold capitalize">
                {leaderboard.data.key_type}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {leaderboard.data.rankings
              .slice(0, expanded ? 100 : PRE_EXPANDED_ROWS)
              .map((r, i) => {
                const rank = i + 1;
                const isTopThree = rank <= 3;
                const rankColors = {
                  1: 'bg-yellow-500/10 border-l-4 border-l-yellow-500 text-yellow-600 dark:text-yellow-400',
                  2: 'bg-gray-400/10 border-l-4 border-l-gray-400 text-gray-600 dark:text-gray-400',
                  3: 'bg-orange-600/10 border-l-4 border-l-orange-600 text-orange-600 dark:text-orange-500',
                };

                return (
                  <TableRow
                    key={i}
                    className={cn(
                      'transition-colors hover:bg-muted/50',
                      isTopThree && rankColors[rank as 1 | 2 | 3],
                    )}
                  >
                    <TableCell
                      className={cn(
                        'text-center font-semibold tabular-nums',
                        isTopThree && 'text-base',
                      )}
                    >
                      {r.value}
                    </TableCell>
                    <TableCell className="py-3 pl-4 text-left">
                      <LeaderboardKeyList
                        cutoffSize={MAX_KEYS_PER_ROW}
                        keyType={leaderboard.data.key_type}
                        keyVals={r.keys}
                        contextTooltipMap={contextTooltipMap}
                        year={year}
                      />
                    </TableCell>
                  </TableRow>
                );
              })}
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
        <Fragment key={k}>
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
        </Fragment>
      ))}
      {keyVals.length > cutoffSize && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger className="italic">
              &nbsp;(and{' '}
              {pluralize(keyVals.length - cutoffSize, 'other', 'others')})
            </TooltipTrigger>
            <TooltipContent
              className="max-w-[500px] text-center break-words
                whitespace-normal"
            >
              <p>
                {keyVals.map((k, i) => (
                  <Fragment key={k}>
                    {i > 0 && ', '}
                    <LeaderboardKeyLink
                      keyType={keyType}
                      keyVal={k}
                      year={year}
                    />
                  </Fragment>
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
  if (keyType === 'event') {
    return (
      <Link to="/event/$eventKey" params={{ eventKey: keyVal }}>
        {keyVal}
      </Link>
    );
  }
  if (keyType === 'match') {
    return <MatchLink matchOrKey={keyVal}>{keyVal}</MatchLink>;
  }
}
