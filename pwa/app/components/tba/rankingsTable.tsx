import { Link } from 'react-router';
import type { ColumnDef } from '@tanstack/react-table';

import BiTrophy from '~icons/bi/trophy';

import { EventRanking } from '~/api/v3';
import { DataTable } from '~/components/tba/dataTable';
import { cn } from '~/lib/utils';

import InlineIcon from './inlineIcon';

type RankingColumnType = ColumnDef<EventRanking['rankings'][number]>[];

export default function RankingsTable({
  rankings,
  winners,
}: {
  rankings: EventRanking;
  winners: string[];
}) {
  const standardCols: RankingColumnType = [
    { header: 'Rank', accessorKey: 'rank', sortDescFirst: false },
    {
      header: 'Team',
      cell: ({ row }) => (
        <Link
          to={`/team/${row.original.team_key.substring(3)}`}
          className="whitespace-nowrap"
        >
          {winners.includes(row.original.team_key) ? (
            <InlineIcon className="relative right-[1ch] justify-center">
              <BiTrophy />
              {row.original.team_key.substring(3)}
            </InlineIcon>
          ) : (
            <>{row.original.team_key.substring(3)}</>
          )}
        </Link>
      ),
      accessorFn: (row) => Number(row.team_key.substring(3)),
      sortDescFirst: false,
    },
  ];

  const sortOrderCols: RankingColumnType = rankings.sort_order_info.map(
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
          'bg-yellow-100 shadow-inner shadow-yellow-200 font-bold':
            winners.includes(row.original.team_key),
        })
      }
    />
  );
}
