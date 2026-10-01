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

interface PlayoffAdvancement2015TableProps {
  advancements: PlayoffAdvancement[];
  year: number;
}

export default function PlayoffAdvancement2015Table({
  advancements,
  year,
}: PlayoffAdvancement2015TableProps): JSX.Element | null {
  const averageScoreAdvancements = advancements.filter(
    (advancement) => advancement.type === 'average_score',
  );

  if (averageScoreAdvancements.length === 0) {
    return null;
  }

  return (
    <div className="mt-4">
      <h2 className="mb-2 text-xl font-medium">Playoff Advancement</h2>

      {averageScoreAdvancements.map((advancement) => {
        const rankings = advancement.rankings ?? [];
        const scoreInfo = advancement.sort_order_info[0];
        const advanceInfo = advancement.extra_stats_info[0];

        return (
          <section key={advancement.level} className="mb-4">
            <h3 className="mb-2 text-lg font-medium">
              {advancement.level_name}
            </h3>

            <Table>
              <TableHeader>
                <TableRow className="*:h-8 *:text-center *:text-foreground">
                  <TableHead>Rank</TableHead>
                  <TableHead>Alliance</TableHead>
                  <TableHead>Teams</TableHead>
                  <TableHead>{scoreInfo?.name ?? 'Average Score'}</TableHead>
                  {advanceInfo && <TableHead>{advanceInfo.name}</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {rankings.map((row, index) => (
                  <TableRow key={row.alliance_name} className="text-center">
                    <TableCell>{row.rank ?? index + 1}</TableCell>
                    <TableCell>{row.alliance_name}</TableCell>
                    <TableCell className="whitespace-nowrap">
                      {row.team_keys.map((teamKey, teamIndex) => (
                        <span key={teamKey}>
                          <TeamLinkWithTooltip teamKey={teamKey} year={year} />
                          {teamIndex < row.team_keys.length - 1 && ', '}
                        </span>
                      ))}
                    </TableCell>
                    <TableCell>
                      {row.sort_orders[0]?.toFixed(scoreInfo?.precision ?? 2) ??
                        '—'}
                    </TableCell>
                    {advanceInfo && (
                      <TableCell>
                        {row.extra_stats[0] ? (
                          <BiCheck
                            className="mx-auto"
                            aria-label={advanceInfo.name}
                          />
                        ) : null}
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </section>
        );
      })}
    </div>
  );
}
