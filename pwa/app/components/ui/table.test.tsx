import { render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { describe, expect, test } from 'vitest';

import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';

describe('Table', () => {
  test('renders a full table with merged classes and forwarded refs', () => {
    const tableRef = createRef<HTMLTableElement>();
    const rowRef = createRef<HTMLTableRowElement>();

    render(
      <Table ref={tableRef} className="group/table">
        <TableCaption className="group/caption">Rankings</TableCaption>
        <TableHeader className="group/header">
          <TableRow>
            <TableHead className="group/head">Team</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody className="group/body">
          <TableRow ref={rowRef} className="group/row">
            <TableCell className="group/cell">254</TableCell>
          </TableRow>
        </TableBody>
        <TableFooter className="group/footer">
          <TableRow>
            <TableCell>Total</TableCell>
          </TableRow>
        </TableFooter>
      </Table>,
    );

    const table = screen.getByRole('table');
    expect(tableRef.current).toBe(table);
    expect(table.className).toContain('group/table');
    expect(table.parentElement?.className).toContain('overflow-auto');

    const caption = screen.getByText('Rankings');
    expect(caption.tagName).toBe('CAPTION');
    expect(caption.className).toContain('group/caption');

    expect(table.querySelector('thead')?.className).toContain('group/header');
    expect(table.querySelector('tbody')?.className).toContain('group/body');
    expect(table.querySelector('tfoot')?.className).toContain('group/footer');

    const head = screen.getByRole('columnheader', { name: 'Team' });
    expect(head.className).toContain('group/head');

    const row = screen.getByText('254').closest('tr');
    expect(rowRef.current).toBe(row);
    expect(row?.className).toContain('group/row');
    expect(screen.getByText('254').className).toContain('group/cell');
  });
});
