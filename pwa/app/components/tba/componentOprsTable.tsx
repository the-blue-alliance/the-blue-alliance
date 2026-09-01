import type { ColumnVisibilityState } from '@tanstack/react-table';
import { useState } from 'react';

import type { EventCoprs } from '~/api/tba/read';
import {
  ColumnVisibilityMenu,
  DataTable,
  type TbaColumnDef,
} from '~/components/tba/dataTable';
import { TeamLinkWithTooltip } from '~/components/tba/teamTooltip';
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card';
import { useMediaQuery } from '~/lib/hooks';
import { type CoprRow, buildCoprTableModel } from '~/lib/oprUtils';
import { camelCaseToHumanReadable } from '~/lib/utils';

export function ComponentOprsTable({
  coprs,
  year,
}: {
  coprs: EventCoprs;
  year: number;
}) {
  const { componentNames, defaultVisible, defaultSortComponent, rows } =
    buildCoprTableModel(coprs, year);

  const isDesktop = useMediaQuery('(min-width: 768px)');
  const [chosenVisibility, setChosenVisibility] =
    useState<ColumnVisibilityState | null>(null);

  const columnVisibility =
    chosenVisibility ??
    (isDesktop
      ? defaultVisible
      : Object.fromEntries(
          componentNames.map((name) => [name, name === defaultSortComponent]),
        ));

  const columns: TbaColumnDef<CoprRow>[] = [
    {
      id: 'team',
      header: 'Team',
      accessorFn: (row) => row.teamKey,
      enableHiding: false,
      cell: (cell) => (
        <TeamLinkWithTooltip teamKey={cell.getValue<string>()} year={year} />
      ),
    },
    ...componentNames.map<TbaColumnDef<CoprRow>>((name) => ({
      id: name,
      header: camelCaseToHumanReadable(name),
      accessorFn: (row) => row.values[name] ?? null,
      cell: (cell) => {
        const value = cell.getValue<number | null>();
        return value === null ? '—' : value.toFixed(2);
      },
    })),
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-4">
          <CardTitle>Component OPRs</CardTitle>
          <ColumnVisibilityMenu
            columns={componentNames.map((name) => ({
              id: name,
              label: camelCaseToHumanReadable(name),
            }))}
            visibility={columnVisibility}
            onVisibilityChange={setChosenVisibility}
          />
        </div>
      </CardHeader>
      <CardContent>
        <DataTable
          columns={columns}
          data={rows}
          equalColumnWidths
          columnVisibility={columnVisibility}
          initialSorting={
            defaultSortComponent
              ? [{ id: defaultSortComponent, desc: true }]
              : []
          }
        />
      </CardContent>
    </Card>
  );
}
