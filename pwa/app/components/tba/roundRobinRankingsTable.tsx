import { type JSX } from 'react';

import BiCheck from '~icons/bi/check-lg';

import { type PlayoffAdvancement } from '~/api/tba/read';
import { TeamLinkWithTooltip } from '~/components/tba/teamTooltip';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { remapTeamKeys } from '~/lib/teamRemap';

interface RoundRobinRankingsTableProps {
  advancement: PlayoffAdvancement;
  year: number;
  remapTeams?: Record<string, string> | null;
}

export default function RoundRobinRankingsTable({
  advancement,
  year,
  remapTeams,
}: RoundRobinRankingsTableProps): JSX.Element {
  const rankings = advancement.rankings ?? [];
  const tiebreakerInfo = advancement.sort_order_info.slice(1);
  const showAdvance = advancement.extra_stats_info.length > 0;

  return (
    <>
      <h2 className="mt-4 mb-2 text-xl font-medium">
        {advancement.level_name}
      </h2>

      <Table>
        <TableHeader>
          <TableRow className="*:h-8 *:text-center *:text-foreground">
            <TableHead>Rank</TableHead>
            <TableHead>Alliance</TableHead>
            <TableHead>Teams</TableHead>
            <TableHead>Record</TableHead>
            <TableHead>
              {advancement.sort_order_info[0]?.name ?? 'Points'}
            </TableHead>
            {tiebreakerInfo.map((info) => (
              <TableHead key={info.name}>{info.name}</TableHead>
            ))}
            {showAdvance && (
              <TableHead>{advancement.extra_stats_info[0].name}</TableHead>
            )}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rankings.map((row, idx) => {
            const teamKeys = remapTeamKeys(row.team_keys, remapTeams);
            return (
              <TableRow key={row.alliance_name} className="text-center">
                <TableCell>{row.rank ?? idx + 1}</TableCell>
                <TableCell>{row.alliance_name}</TableCell>
                <TableCell className="whitespace-nowrap">
                  {teamKeys.map((teamKey, i) => (
                    <span key={teamKey}>
                      <TeamLinkWithTooltip teamKey={teamKey} year={year} />
                      {i < teamKeys.length - 1 && ', '}
                    </span>
                  ))}
                </TableCell>
                <TableCell>
                  {row.record
                    ? `${row.record.wins}-${row.record.losses}-${row.record.ties}`
                    : '—'}
                </TableCell>
                <TableCell>{row.sort_orders[0]}</TableCell>
                {tiebreakerInfo.map((info, i) => (
                  <TableCell key={info.name}>
                    {row.sort_orders[i + 1]}
                  </TableCell>
                ))}
                {showAdvance && (
                  <TableCell>
                    {row.extra_stats[0] ? (
                      <BiCheck className="mx-auto" aria-label="Advances" />
                    ) : null}
                  </TableCell>
                )}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </>
  );
}
