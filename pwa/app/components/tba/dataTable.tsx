import {
  type ColumnDef,
  type ColumnVisibilityState,
  FlexRender,
  type Row,
  type RowData,
  type SortingState,
  columnSizingFeature,
  columnVisibilityFeature,
  createSortedRowModel,
  rowSortingFeature,
  sortFn_alphanumeric,
  sortFn_datetime,
  sortFn_text,
  tableFeatures,
  useTable,
} from '@tanstack/react-table';
import { useWindowVirtualizer } from '@tanstack/react-virtual';
import { cn } from 'cn';
import { useLayoutEffect, useRef, useState } from 'react';

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

// The built-in sort functions have to be registered here, otherwise a column's
// default `sortFn: 'auto'` cannot resolve one.
export const tbaTableFeatures = tableFeatures({
  rowSortingFeature,
  columnVisibilityFeature,
  columnSizingFeature,
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
  enableSortingRemoval?: boolean;
  columnVisibility?: ColumnVisibilityState;
  equalColumnWidths?: boolean;
  virtualized?: boolean;
}

type TbaRow<TData extends RowData> = Row<typeof tbaTableFeatures, TData>;

function VirtualizedRows<TData extends RowData>({
  rows,
  conditionalRowStyling,
}: {
  rows: TbaRow<TData>[];
  conditionalRowStyling?: (row: TbaRow<TData>) => string;
}) {
  const topSpacerRef = useRef<HTMLTableRowElement>(null);
  const [scrollMargin, setScrollMargin] = useState(0);

  useLayoutEffect(() => {
    const top = topSpacerRef.current?.getBoundingClientRect().top ?? 0;
    setScrollMargin(top + window.scrollY);
  }, []);

  const virtualizer = useWindowVirtualizer({
    count: rows.length,
    estimateSize: () => 41,
    overscan: 10,
    scrollMargin,
    initialRect: { width: 0, height: 1000 },
  });

  const items = virtualizer.getVirtualItems();
  const firstItem = items.at(0);
  const lastItem = items.at(-1);
  const paddingTop = firstItem ? firstItem.start - scrollMargin : 0;
  const paddingBottom = lastItem
    ? virtualizer.getTotalSize() - (lastItem.end - scrollMargin)
    : 0;

  return (
    <>
      <tr ref={topSpacerRef} aria-hidden style={{ height: paddingTop }} />
      {items.map((item) => (
        <TableRow
          key={rows[item.index].id}
          ref={virtualizer.measureElement}
          data-index={item.index}
          className={cn(
            item.index % 2 === 0 ? 'bg-muted/30' : 'odd:bg-transparent',
            conditionalRowStyling?.(rows[item.index]),
          )}
        >
          {rows[item.index].getVisibleCells().map((cell) => (
            <TableCell key={cell.id} className="text-center">
              <FlexRender cell={cell} />
            </TableCell>
          ))}
        </TableRow>
      ))}
      <tr aria-hidden style={{ height: paddingBottom }} />
    </>
  );
}

export function DataTable<TData extends RowData>({
  columns,
  data,
  initialSorting,
  enableSortingRemoval = true,
  columnVisibility,
  equalColumnWidths,
  virtualized,
  conditionalRowStyling,
}: DataTableProps<TData> & {
  conditionalRowStyling?: (row: Row<typeof tbaTableFeatures, TData>) => string;
}) {
  const [sorting, setSorting] = useState<SortingState>(initialSorting ?? []);
  const table = useTable({
    features: tbaTableFeatures,
    data,
    columns,
    enableSortingRemoval,
    onSortingChange: setSorting,
    state: { sorting, columnVisibility: columnVisibility ?? {} },
  });

  const visibleColumnCount = table.getVisibleLeafColumns().length;

  return (
    <div className="overflow-x-auto">
      <Table
        className={cn(
          'mx-auto',
          (equalColumnWidths || virtualized) && 'table-fixed',
        )}
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
                  <TableHead
                    key={header.id}
                    style={
                      virtualized ? { width: header.getSize() } : undefined
                    }
                  >
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
            virtualized ? (
              <VirtualizedRows
                rows={table.getRowModel().rows}
                conditionalRowStyling={conditionalRowStyling}
              />
            ) : (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} className={conditionalRowStyling?.(row)}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="text-center">
                      <FlexRender cell={cell} />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )
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
