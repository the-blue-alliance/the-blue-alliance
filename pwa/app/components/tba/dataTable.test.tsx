import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  ColumnVisibilityMenu,
  DataTable,
  type TbaColumnDef,
} from '~/components/tba/dataTable';

interface Row {
  team: string;
  score: number;
}

const columns: TbaColumnDef<Row>[] = [
  {
    id: 'team',
    header: 'Team',
    accessorFn: (r) => r.team,
    enableSorting: false,
  },
  { id: 'score', header: 'Score', accessorFn: (r) => r.score },
];

const data: Row[] = [
  { team: 'frc254', score: 10 },
  { team: 'frc604', score: 30 },
  { team: 'frc1678', score: 20 },
];

function bodyColumn(index: number) {
  return screen
    .getAllByRole('row')
    .slice(1)
    .map((r) => within(r).getAllByRole('cell')[index].textContent);
}

describe('DataTable', () => {
  test('sorts through ascending, descending, and cleared states', () => {
    render(
      <DataTable
        columns={columns}
        data={data}
        conditionalRowStyling={(row) =>
          row.original.team === 'frc604' ? 'highlight' : ''
        }
      />,
    );
    expect(bodyColumn(1)).toEqual(['10', '30', '20']);
    expect(screen.getByText('Team').closest('button')).toBeNull();
    expect(screen.getByRole('row', { name: 'frc604 30' }).className).toContain(
      'highlight',
    );

    // Numeric columns sort descending first.
    const sort = screen.getByRole('button', { name: 'Score' });
    expect(sort.title).toBe('Sort descending');
    fireEvent.click(sort);
    expect(bodyColumn(1)).toEqual(['30', '20', '10']);
    expect(sort.textContent).toBe('Score ↓');
    expect(sort.title).toBe('Sort ascending');

    fireEvent.click(sort);
    expect(bodyColumn(1)).toEqual(['10', '20', '30']);
    expect(sort.textContent).toBe('Score ↑');
    expect(sort.title).toBe('Clear sort');

    fireEvent.click(sort);
    expect(bodyColumn(1)).toEqual(['10', '30', '20']);
  });

  test('applies initial sorting, visibility, and equal widths', () => {
    render(
      <DataTable
        columns={columns}
        data={data}
        initialSorting={[{ id: 'score', desc: true }]}
        columnVisibility={{ team: false }}
        equalColumnWidths
      />,
    );
    expect(bodyColumn(0)).toEqual(['30', '20', '10']);
    const table = screen.getByRole('table');
    expect(table.className).toContain('table-fixed');
    expect(table.style.minWidth).toBe('6rem');
  });

  test('shows an empty state', () => {
    render(<DataTable columns={columns} data={[]} />);
    const cell = screen.getByRole('cell', { name: 'No results.' });
    expect(cell.getAttribute('colspan')).toBe('2');
  });

  test('renders placeholder headers for grouped columns', () => {
    render(
      <DataTable<Row>
        columns={[
          { id: 'team', header: 'Team', accessorFn: (r) => r.team },
          {
            id: 'group',
            header: 'Group',
            columns: [
              { id: 'score', header: 'Score', accessorFn: (r) => r.score },
            ],
          },
        ]}
        data={data}
      />,
    );
    expect(screen.getAllByRole('columnheader')[0].textContent).toBe('');
  });
});

describe('ColumnVisibilityMenu', () => {
  test('toggles a column', async () => {
    const onVisibilityChange =
      vi.fn<(visibility: Record<string, boolean>) => void>();
    render(
      <ColumnVisibilityMenu
        columns={[
          { id: 'score', label: 'Score' },
          { id: 'rank', label: 'Rank' },
        ]}
        visibility={{ score: false }}
        onVisibilityChange={onVisibilityChange}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Columns' }));

    const score = await screen.findByRole('menuitemcheckbox', {
      name: 'Score',
    });
    const rank = screen.getByRole('menuitemcheckbox', { name: 'Rank' });
    expect(score.getAttribute('aria-checked')).toBe('false');
    expect(rank.getAttribute('aria-checked')).toBe('true');

    fireEvent.click(score);
    expect(onVisibilityChange).toHaveBeenCalledWith({ score: true });
  });
});
