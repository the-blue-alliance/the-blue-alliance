import {
  type ColumnDef,
  type ColumnVisibilityState,
  FlexRender,
  type Row,
  type RowData,
  type SortingState,
  columnVisibilityFeature,
  createSortedRowModel,
  rowSortingFeature,
  sortFn_alphanumeric,
  sortFn_datetime,
  sortFn_text,
  tableFeatures,
  useTable,
} from '@tanstack/react-table';
import { useState } from 'react';

import ColumnsIcon from '~icons/lucide/columns-3';

import { Button } from '~/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { cn } from '~/lib/utils';

// The built-in sort functions have to be registered here, otherwise a column's
// default `sortFn: 'auto'` cannot resolve one.
export const tbaTableFeatures = tableFeatures({
  rowSortingFeature,
  columnVisibilityFeature,
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

export function ColumnVisibilityMenu({
  columns,
  visibility,
  onVisibilityChange,
}: {
  columns: { id: string; label: string }[];
  visibility: ColumnVisibilityState;
  onVisibilityChange: (visibility: ColumnVisibilityState) => void;
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button variant="outline" size="sm" className="cursor-pointer">
            <ColumnsIcon className="mr-1.5 size-4" />
            Columns
          </Button>
        }
      />
      <DropdownMenuContent align="end" className="max-h-[50vh] overflow-y-auto">
        {columns.map(({ id, label }) => (
          <DropdownMenuCheckboxItem
            key={id}
            checked={visibility[id] ?? true}
            onCheckedChange={(checked) =>
              onVisibilityChange({ ...visibility, [id]: checked })
            }
          >
            {label}
          </DropdownMenuCheckboxItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

interface DataTableProps<TData extends RowData> {
  columns: TbaColumnDef<TData>[];
  data: TData[];
  initialSorting?: SortingState;
  columnVisibility?: ColumnVisibilityState;
  equalColumnWidths?: boolean;
}

export function DataTable<TData extends RowData>({
  columns,
  data,
  initialSorting,
  columnVisibility,
  equalColumnWidths,
  conditionalRowStyling,
}: DataTableProps<TData> & {
  conditionalRowStyling?: (row: Row<typeof tbaTableFeatures, TData>) => string;
}) {
  const [sorting, setSorting] = useState<SortingState>(initialSorting ?? []);
  const table = useTable({
    features: tbaTableFeatures,
    data,
    columns,
    onSortingChange: setSorting,
    state: { sorting, columnVisibility: columnVisibility ?? {} },
  });

  const visibleColumnCount = table.getVisibleLeafColumns().length;

  return (
    <div className="overflow-x-auto">
      <Table
        className={cn('mx-auto', equalColumnWidths && 'table-fixed')}
        style={
          equalColumnWidths
            ? { minWidth: `${visibleColumnCount * 6}rem` }
            : undefined
        }
      >
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
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id} className="text-center">
                    <FlexRender cell={cell} />
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell
                colSpan={visibleColumnCount}
                className="h-24 text-center"
              >
                No results.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
