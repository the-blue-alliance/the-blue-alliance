import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { type EventRanking } from '~/api/tba/read';
import { getEventRankingsOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import { TeamLink } from '~/components/tba/links';
import { Spinner } from '~/components/ui/spinner';
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
  TooltipTrigger,
} from '~/components/ui/tooltip';

function getTotalRankingPoints(
  ranking: EventRanking['rankings'][number],
  rankingScoreInfo: NonNullable<EventRanking['sort_order_info']>[number],
): number | undefined {
  const rankingScore = ranking.sort_orders[0];

  if (rankingScoreInfo.name !== 'Ranking Score' || rankingScore === undefined) {
    return undefined;
  }

  if (rankingScoreInfo.precision === 0) {
    return Math.round(rankingScore);
  }

  return Math.round(rankingScore * ranking.matches_played);
}

function StatChip({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-lg bg-muted p-3 text-center">
      <div className="text-xs tracking-wide text-muted-foreground uppercase">
        {label}
      </div>
      <div className="mt-1 text-2xl leading-none font-bold">{value}</div>
      {sub && <div className="mt-1 text-xs text-muted-foreground">{sub}</div>}
    </div>
  );
}

export default function EventRankTooltip({
  eventKey,
  teamKey,
  rank,
  numTeams,
}: {
  eventKey: string;
  teamKey: string;
  rank: number;
  numTeams?: number;
}) {
  const [open, setOpen] = useState(false);
  const [hasOpened, setHasOpened] = useState(false);
  const rankingsQuery = useQuery({
    ...getEventRankingsOptions({ path: { event_key: eventKey } }),
    enabled: hasOpened,
  });

  const rankings = rankingsQuery.data?.rankings.toSorted(
    (a, b) => a.rank - b.rank,
  );
  const rankingScoreInfo = rankingsQuery.data?.sort_order_info?.[0];
  const showRankingPoints =
    Number(eventKey.substring(0, 4)) >= 2016 &&
    rankingScoreInfo?.name === 'Ranking Score';

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);
    if (nextOpen) {
      setHasOpened(true);
    }
  };

  return (
    <Tooltip open={open} onOpenChange={handleOpenChange}>
      <TooltipTrigger
        type="button"
        className="w-full cursor-help"
        aria-label={`Rank ${rank}${numTeams ? ` of ${numTeams}` : ''}; show event rankings`}
        onClick={() => handleOpenChange(!open)}
      >
        <StatChip
          label="Rank"
          value={rank.toString()}
          sub={numTeams ? `of ${numTeams}` : undefined}
        />
      </TooltipTrigger>
      <TooltipContent
        className="max-w-none"
        viewportClassName="max-h-none overflow-visible"
        side="top"
        sideOffset={6}
      >
        {rankingsQuery.isPending ? (
          <div className="flex items-center gap-2 py-2">
            <Spinner />
            <span>Loading rankings…</span>
          </div>
        ) : rankingsQuery.isError ? (
          <div className="py-2">Rankings unavailable.</div>
        ) : !rankings || rankings.length === 0 ? (
          <div className="py-2">No rankings available.</div>
        ) : (
          <div className="max-h-[252px] overflow-y-auto">
            <Table className="min-w-48 text-xs">
              <TableHeader>
                <TableRow className="h-7">
                  <TableHead className="h-7 px-0.5 text-center">Rank</TableHead>
                  <TableHead className="h-7 text-center">Team</TableHead>
                  <TableHead className="h-7 text-center">Record</TableHead>
                  {showRankingPoints && (
                    <TableHead className="h-7 text-center">RP</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {rankings.map((ranking) => (
                  <TableRow
                    key={ranking.team_key}
                    className={
                      ranking.team_key === teamKey
                        ? 'h-7 bg-blue-100! font-semibold dark:bg-blue-500/20!'
                        : 'h-7'
                    }
                    aria-current={
                      ranking.team_key === teamKey ? 'true' : undefined
                    }
                  >
                    <TableCell className="px-0.5 py-0 text-center">
                      {ranking.rank}
                    </TableCell>
                    <TableCell className="py-0 text-center font-medium">
                      <TeamLink
                        teamOrKey={ranking.team_key}
                        year={Number(eventKey.substring(0, 4))}
                      >
                        {ranking.team_key.substring(3)}
                      </TeamLink>
                    </TableCell>
                    <TableCell className="py-0 text-center tabular-nums">
                      {ranking.record
                        ? `${ranking.record.wins}-${ranking.record.losses}-${ranking.record.ties}`
                        : '—'}
                    </TableCell>
                    {showRankingPoints && rankingScoreInfo && (
                      <TableCell className="py-0 text-center tabular-nums">
                        {getTotalRankingPoints(ranking, rankingScoreInfo) ??
                          '—'}
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </TooltipContent>
    </Tooltip>
  );
}
