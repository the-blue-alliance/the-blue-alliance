import {
  type ColumnDef,
  FlexRender,
  type Row,
  type RowData,
  type SortingState,
  createSortedRowModel,
  rowSortingFeature,
  sortFn_alphanumeric,
  sortFn_datetime,
  sortFn_text,
  tableFeatures,
  useTable,
} from '@tanstack/react-table';
import { useState } from 'react';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';

// Sorting is the only table feature we use. The built-in sort functions have to
// be registered here, otherwise a column's default `sortFn: 'auto'` cannot
// resolve one.
export const tbaTableFeatures = tableFeatures({
  rowSortingFeature,
  sortedRowModel: createSortedRowModel(),
  sortFns: {
    alphanumeric: sortFn_alphanumeric,
    datetime: sortFn_datetime,
    text: sortFn_text,
  },
});

export type TbaColumnDef<TData extends RowData> = ColumnDef<
  typeof tbaTableFeatures,
  TData
>;

interface DataTableProps<TData extends RowData> {
  columns: TbaColumnDef<TData>[];
  data: TData[];
}

export function DataTable<TData extends RowData>({
  columns,
  data,
  conditionalRowStyling,
}: DataTableProps<TData> & {
  conditionalRowStyling?: (row: Row<typeof tbaTableFeatures, TData>) => string;
}) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const table = useTable({
    features: tbaTableFeatures,
    data,
    columns,
    onSortingChange: setSorting,
    state: { sorting },
  });

  return (
    <div className="overflow-x-auto">
      <Table className="mx-auto">
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                if (header.isPlaceholder) {
                  return <TableHead key={header.id} />;
                }

                const content = (
                  <>
                    <FlexRender header={header} />
                    {{
                      asc: ' ↑',
                      desc: ' ↓',
                    }[header.column.getIsSorted() as string] ?? null}
                  </>
                );

                return (
                  <TableHead key={header.id}>
                    {header.column.getCanSort() ? (
                      <button
                        type="button"
                        className="w-full cursor-pointer text-center
                          select-none"
                        onClick={header.column.getToggleSortingHandler()}
                        title={
                          header.column.getNextSortingOrder() === 'asc'
                            ? 'Sort ascending'
                            : header.column.getNextSortingOrder() === 'desc'
                              ? 'Sort descending'
                              : 'Clear sort'
                        }
                      >
                        {content}
                      </button>
                    ) : (
                      content
                    )}
                  </TableHead>
                );
              })}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow key={row.id} className={conditionalRowStyling?.(row)}>
                {row.getAllCells().map((cell) => (
                  <TableCell key={cell.id} className="text-center">
                    <FlexRender cell={cell} />
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
