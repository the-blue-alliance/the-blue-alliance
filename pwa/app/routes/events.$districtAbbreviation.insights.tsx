import {
  ColumnDef,
  SortingState,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { useState } from 'react';
import { useLoaderData } from 'react-router';
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts';

import {
  DistrictInsight,
  getDistrictHistory,
  getDistrictInsights,
} from '~/api/tba/read';
import { TeamLink } from '~/components/tba/links';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from '~/components/ui/chart';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { confidence } from '~/lib/utils';

import { Route } from '.react-router/types/app/routes/+types/events.$districtAbbreviation.insights';

async function loadData(params: Route.LoaderArgs['params']) {
  const [history, insights] = await Promise.all([
    await getDistrictHistory({
      path: {
        district_abbreviation: params.districtAbbreviation,
      },
    }),
    await getDistrictInsights({
      path: {
        district_abbreviation: params.districtAbbreviation,
      },
    }),
  ]);

  if (history.data === undefined || insights.data === undefined) {
    throw new Response(null, { status: 404 });
  }

  return {
    history: history.data,
    insights: insights.data,
  };
}

export async function loader({ params }: Route.LoaderArgs) {
  return await loadData(params);
}

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return await loadData(params);
}

export function meta({ data }: Route.MetaArgs) {
  return [
    {
      title: `${data.history[data.history.length - 1].display_name} District Insights - The Blue Alliance`,
    },
  ];
}

export default function DistrictPage() {
  const { history, insights } = useLoaderData<typeof loader>();

  return (
    <div>
      <h1 className="mb-4 text-3xl font-bold">
        {history[history.length - 1].display_name} District Insights
      </h1>

      <Tabs defaultValue="Growth">
        <TabsList className="flex h-auto flex-wrap items-center justify-evenly *:basis-1/2 lg:*:basis-1">
          <TabsTrigger value="Growth">Growth</TabsTrigger>
          <TabsTrigger value="Team">Team Data</TabsTrigger>
        </TabsList>

        <TabsContent value="Growth">
          <DistrictDataView districtData={insights.district_data} />
        </TabsContent>

        <TabsContent value="Team">
          <TeamDataView teamData={insights.team_data ?? {}} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function DistrictDataView({
  districtData,
}: {
  districtData: DistrictInsight['district_data'];
}) {
  if (districtData === null) {
    return null;
  }

  return (
    <div>
      <div className="flex flex-row flex-wrap gap-4 md:flex-nowrap [&>*]:w-full md:[&>*]:w-1/2">
        <div className="flex flex-col">
          <h1 className="mb-2 text-center text-xl">Yearly Active Team Count</h1>
          <ChartContainer config={{}} className="min-h-[100px] w-full">
            <BarChart
              data={Object.entries(
                districtData.district_wide_data?.yearly_active_team_count ?? {},
              ).map(([year, count]) => ({
                year: Number(year),
                count,
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Bar
                type="monotone"
                dataKey="count"
                fill="var(--color-primary)"
              />
              <ChartTooltip content={<ChartTooltipContent />} />
            </BarChart>
          </ChartContainer>
        </div>

        <div className="flex flex-col">
          <h1 className="mb-2 text-center text-xl">Yearly Event Count</h1>
          <ChartContainer config={{}} className="min-h-[100px] w-full">
            <BarChart
              data={Object.entries(
                districtData.district_wide_data?.yearly_event_count ?? {},
              ).map(([year, count]) => ({
                year: Number(year),
                count,
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Bar
                type="monotone"
                dataKey="count"
                fill="var(--color-primary)"
              />
              <ChartTooltip content={<ChartTooltipContent />} />
            </BarChart>
          </ChartContainer>
        </div>
      </div>
    </div>
  );
}

type TeamDataEntryWithKey = NonNullable<
  DistrictInsight['team_data']
>[string] & {
  teamKey: string;
};
function TeamDataView({
  teamData,
}: {
  teamData: DistrictInsight['team_data'];
}) {
  if (teamData === null) {
    return null;
  }

  const rows: TeamDataEntryWithKey[] = Object.entries(teamData)
    .map(([teamKey, teamData]) => ({
      ...teamData,
      teamKey,
    }))
    .toSorted(
      (a, b) => Number(a.teamKey.substring(3)) - Number(b.teamKey.substring(3)),
    );

  const columns: ColumnDef<TeamDataEntryWithKey>[] = [
    {
      header: 'Team',
      accessorKey: 'teamKey',
      cell: ({ row }) => {
        return (
          <TeamLink teamOrKey={row.original.teamKey} year={0}>
            {row.original.teamKey.substring(3)}
          </TeamLink>
        );
      },
    },
    {
      header: 'District Seasons',
      accessorKey: 'district_seasons',
    },
    {
      header: 'Average District Points',
      accessorFn: (row) => {
        return (row.total_district_points / row.district_seasons).toFixed(1);
      },
    },
    {
      header: 'Average Pre-DCMP District Points',
      accessorFn: (row) => {
        return (
          row.total_pre_dcmp_district_points / row.district_seasons
        ).toFixed(1);
      },
    },
    {
      header: 'District Event Wins',
      accessorKey: 'district_event_wins',
    },
    {
      header: 'DCMP Wins',
      accessorKey: 'dcmp_wins',
    },
    {
      header: 'Team Awards',
      accessorKey: 'team_awards',
    },
    {
      header: 'Individual Awards',
      accessorKey: 'individual_awards',
    },
    {
      header: 'Qual Record',
      accessorFn: (row) => {
        return `${row.quals_record.wins}-${row.quals_record.losses}-${row.quals_record.ties}`;
      },
      sortingFn: (rowA, rowB) => {
        return (
          confidence(
            rowA.original.quals_record.wins,
            rowA.original.quals_record.losses,
          ) -
          confidence(
            rowB.original.quals_record.wins,
            rowB.original.quals_record.losses,
          )
        );
      },
    },
    {
      header: 'Elim Record',
      accessorFn: (row) => {
        return `${row.elims_record.wins}-${row.elims_record.losses}-${row.elims_record.ties}`;
      },
      sortingFn: (rowA, rowB) => {
        return (
          confidence(
            rowA.original.quals_record.wins,
            rowA.original.quals_record.losses,
          ) -
          confidence(
            rowB.original.quals_record.wins,
            rowB.original.quals_record.losses,
          )
        );
      },
    },
    {
      header: 'Total Record',
      accessorFn: (row) => {
        const wins = row.quals_record.wins + row.elims_record.wins;
        const losses = row.quals_record.losses + row.elims_record.losses;
        const ties = row.quals_record.ties + row.elims_record.ties;
        return `${wins}-${losses}-${ties}`;
      },
      sortingFn: (rowA, rowB) => {
        return (
          confidence(
            rowA.original.quals_record.wins + rowA.original.elims_record.wins,
            rowA.original.quals_record.losses +
              rowA.original.elims_record.losses,
          ) -
          confidence(
            rowB.original.quals_record.wins + rowB.original.elims_record.wins,
            rowB.original.quals_record.losses +
              rowB.original.elims_record.losses,
          )
        );
      },
    },
  ];

  return (
    <div>
      <TeamDataTable columns={columns} data={rows} />
    </div>
  );
}

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
}

function TeamDataTable<TData, TValue>({
  columns,
  data,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    state: {
      sorting,
    },
  });

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                return (
                  <TableHead
                    key={header.id}
                    className="cursor-pointer text-center"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext(),
                        )}
                  </TableHead>
                );
              })}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows?.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                data-state={row.getIsSelected() && 'selected'}
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id} className="text-center">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                No results.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
