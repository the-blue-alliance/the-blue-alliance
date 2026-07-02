import type { ColumnDef } from '@tanstack/react-table';

import { EventRanking } from '~/api/tba/read';
import { DataTable } from '~/components/tba/dataTable';
import { TeamLinkWithTooltip } from '~/components/tba/teamTooltip';
import { cn } from '~/lib/utils';

type RankingColumnType = ColumnDef<EventRanking['rankings'][number]>[];

export default function RankingsTable({
  rankings,
  winners,
  captains,
  year,
}: {
  rankings: EventRanking;
  winners: string[];
  captains: string[];
  year: number;
}) {
  const standardCols: RankingColumnType = [
    { header: 'Rank', accessorKey: 'rank', sortDescFirst: false },
    {
      header: 'Team',
      cell: ({ row }) => {
        const teamKey = row.original.team_key;
        const isWinner = winners.includes(teamKey);
        const isCaptain = captains.includes(teamKey);
        return (
          <TeamLinkWithTooltip
            teamKey={row.original.team_key}
            year={year}
            isWinner={isWinner}
            isCaptain={isCaptain}
          />
        );
      },
      accessorFn: (row) => Number(row.team_key.substring(3)),
      sortDescFirst: false,
    },
  ];

  const sortOrderCols: RankingColumnType = (rankings.sort_order_info ?? []).map(
    (sortOrder, idx) => ({
      header: sortOrder.name,
      accessorFn: (row) => row.sort_orders?.[idx].toFixed(sortOrder.precision),
      sortDescFirst: true,
    }),
  );

  const wlt: RankingColumnType =
    rankings.rankings[0]?.record === null
      ? []
      : [
          {
            header: 'Record (W-L-T)',
            accessorFn: (row) =>
              row.record &&
              `${row.record.wins}-${row.record.losses}-${row.record.ties}`,
            sortDescFirst: true,
            sortingFn: (a, b) => {
              if (a.original.record === null || b.original.record === null) {
                return 0;
              }
              const aRP = 2 * a.original.record.wins + a.original.record.ties;
              const bRP = 2 * b.original.record.wins + b.original.record.ties;
              return aRP - bRP;
            },
          },
        ];

  const summaryCols: RankingColumnType = [
    ...wlt,
    {
      header: 'DQ',
      accessorFn: (row) => row.dq,
      sortDescFirst: true,
    },
    {
      header: 'Played',
      accessorFn: (row) => row.matches_played,
      sortDescFirst: true,
    },
  ];

  const generatedCols: RankingColumnType = rankings.extra_stats_info.map(
    (stat, idx) => ({
      header: stat.name,
      accessorFn: (row) => row.extra_stats[idx],
      sortDescFirst: true,
    }),
  );

  return (
    <DataTable
      columns={standardCols
        .concat(sortOrderCols)
        .concat(summaryCols)
        .concat(generatedCols)}
      data={rankings.rankings}
      conditionalRowStyling={(row) =>
        cn({
          [`bg-yellow-100! font-bold shadow-inner shadow-yellow-200
          dark:bg-yellow-500/15! dark:shadow-yellow-500/10`]: winners.includes(
            row.original.team_key,
          ),
        })
      }
    />
  );
}
