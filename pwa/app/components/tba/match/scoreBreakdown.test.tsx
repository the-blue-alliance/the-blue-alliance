import { render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  ScoreBreakdownAllianceCell,
  ScoreBreakdownLabelCell,
  ScoreBreakdownRow,
  ScoreBreakdownTable,
} from '~/components/tba/match/scoreBreakdown';

vi.mock('~icons/mdi/arrow-left', () => ({
  default: () => <img alt="Red leads" />,
}));

vi.mock('~icons/mdi/arrow-right', () => ({
  default: () => <img alt="Blue leads" />,
}));

describe('ScoreBreakdownTable', () => {
  test('renders its rows inside a table', () => {
    render(
      <ScoreBreakdownTable>
        <ScoreBreakdownRow>
          <ScoreBreakdownAllianceCell color="red">
            10
          </ScoreBreakdownAllianceCell>
          <ScoreBreakdownLabelCell>Auto</ScoreBreakdownLabelCell>
          <ScoreBreakdownAllianceCell color="blue">
            20
          </ScoreBreakdownAllianceCell>
        </ScoreBreakdownRow>
      </ScoreBreakdownTable>,
    );

    expect(within(screen.getByRole('table')).getByRole('row')).toBeTruthy();
  });

  test('renders each cell of a row', () => {
    render(
      <ScoreBreakdownTable>
        <ScoreBreakdownRow>
          <ScoreBreakdownAllianceCell color="red">
            10
          </ScoreBreakdownAllianceCell>
          <ScoreBreakdownLabelCell>Auto</ScoreBreakdownLabelCell>
          <ScoreBreakdownAllianceCell color="blue">
            20
          </ScoreBreakdownAllianceCell>
        </ScoreBreakdownRow>
      </ScoreBreakdownTable>,
    );

    expect(screen.getAllByRole('cell').map((cell) => cell.textContent)).toEqual(
      ['10', 'Auto', '20'],
    );
  });
});

describe('ScoreBreakdownRow', () => {
  test('points the label at red when red scored more', () => {
    render(
      <table>
        <tbody>
          <ScoreBreakdownRow redValue={12} blueValue={4}>
            <ScoreBreakdownAllianceCell color="red">
              12
            </ScoreBreakdownAllianceCell>
            <ScoreBreakdownLabelCell>Auto</ScoreBreakdownLabelCell>
            <ScoreBreakdownAllianceCell color="blue">
              4
            </ScoreBreakdownAllianceCell>
          </ScoreBreakdownRow>
        </tbody>
      </table>,
    );

    expect(screen.getByRole('img', { name: 'Red leads' })).toBeTruthy();
    expect(screen.queryByRole('img', { name: 'Blue leads' })).toBeNull();
  });

  test('points the label at blue when blue scored more', () => {
    render(
      <table>
        <tbody>
          <ScoreBreakdownRow redValue={4} blueValue={12}>
            <ScoreBreakdownAllianceCell color="red">
              4
            </ScoreBreakdownAllianceCell>
            <ScoreBreakdownLabelCell>Auto</ScoreBreakdownLabelCell>
            <ScoreBreakdownAllianceCell color="blue">
              12
            </ScoreBreakdownAllianceCell>
          </ScoreBreakdownRow>
        </tbody>
      </table>,
    );

    expect(screen.getByRole('img', { name: 'Blue leads' })).toBeTruthy();
    expect(screen.queryByRole('img', { name: 'Red leads' })).toBeNull();
  });

  test('shows no arrow when both alliances scored the same', () => {
    render(
      <table>
        <tbody>
          <ScoreBreakdownRow redValue={8} blueValue={8}>
            <ScoreBreakdownAllianceCell color="red">
              8
            </ScoreBreakdownAllianceCell>
            <ScoreBreakdownLabelCell>Auto</ScoreBreakdownLabelCell>
            <ScoreBreakdownAllianceCell color="blue">
              8
            </ScoreBreakdownAllianceCell>
          </ScoreBreakdownRow>
        </tbody>
      </table>,
    );

    expect(screen.queryByRole('img')).toBeNull();
  });

  test('shows no arrow when no values are given', () => {
    render(
      <table>
        <tbody>
          <ScoreBreakdownRow>
            <ScoreBreakdownAllianceCell color="red">
              -
            </ScoreBreakdownAllianceCell>
            <ScoreBreakdownLabelCell>RP</ScoreBreakdownLabelCell>
            <ScoreBreakdownAllianceCell color="blue">
              -
            </ScoreBreakdownAllianceCell>
          </ScoreBreakdownRow>
        </tbody>
      </table>,
    );

    expect(screen.queryByRole('img')).toBeNull();
  });

  test('treats a missing red value as zero', () => {
    render(
      <table>
        <tbody>
          <ScoreBreakdownRow blueValue={3}>
            <ScoreBreakdownAllianceCell color="red">
              0
            </ScoreBreakdownAllianceCell>
            <ScoreBreakdownLabelCell>Auto</ScoreBreakdownLabelCell>
            <ScoreBreakdownAllianceCell color="blue">
              3
            </ScoreBreakdownAllianceCell>
          </ScoreBreakdownRow>
        </tbody>
      </table>,
    );

    expect(screen.getByRole('img', { name: 'Blue leads' })).toBeTruthy();
  });

  test('treats a missing blue value as zero', () => {
    render(
      <table>
        <tbody>
          <ScoreBreakdownRow redValue={3}>
            <ScoreBreakdownAllianceCell color="red">
              3
            </ScoreBreakdownAllianceCell>
            <ScoreBreakdownLabelCell>Auto</ScoreBreakdownLabelCell>
            <ScoreBreakdownAllianceCell color="blue">
              0
            </ScoreBreakdownAllianceCell>
          </ScoreBreakdownRow>
        </tbody>
      </table>,
    );

    expect(screen.getByRole('img', { name: 'Red leads' })).toBeTruthy();
  });

  test('passes non-element children through untouched', () => {
    render(
      <table>
        <tbody>
          <ScoreBreakdownRow redValue={1} blueValue={0}>
            <td>plain cell</td>
          </ScoreBreakdownRow>
        </tbody>
      </table>,
    );

    expect(screen.getByRole('row').textContent).toBe('plain cell');
  });

  test('gives win flags only to the label cell', () => {
    function PropsProbe(props: Record<string, unknown>) {
      return <td>{Object.keys(props).sort().join(',')}</td>;
    }
    render(
      <table>
        <tbody>
          <ScoreBreakdownRow redValue={1} blueValue={0}>
            <PropsProbe color="red" />
          </ScoreBreakdownRow>
        </tbody>
      </table>,
    );

    expect(screen.getByRole('cell').textContent).toBe('color');
  });
});

describe('ScoreBreakdownAllianceCell', () => {
  test.each([
    { color: 'red' as const, shade: 'light' as const },
    { color: 'red' as const, shade: 'dark' as const },
    { color: 'blue' as const, shade: 'light' as const },
    { color: 'blue' as const, shade: 'dark' as const },
    { color: 'neutral' as const, shade: 'light' as const },
    { color: 'neutral' as const, shade: 'dark' as const },
  ])('renders its content as a $shade $color cell', ({ color, shade }) => {
    render(
      <table>
        <tbody>
          <tr>
            <ScoreBreakdownAllianceCell color={color} shade={shade}>
              42
            </ScoreBreakdownAllianceCell>
          </tr>
        </tbody>
      </table>,
    );

    expect(screen.getByRole('cell').textContent).toBe('42');
  });

  test('renders bold content', () => {
    render(
      <table>
        <tbody>
          <tr>
            <ScoreBreakdownAllianceCell color="red" fontWeight="bold">
              99
            </ScoreBreakdownAllianceCell>
          </tr>
        </tbody>
      </table>,
    );

    expect(screen.getByRole('cell').textContent).toBe('99');
  });
});

describe('ScoreBreakdownLabelCell', () => {
  test('renders its label', () => {
    render(
      <table>
        <tbody>
          <tr>
            <ScoreBreakdownLabelCell shade="dark" fontWeight="bold">
              Total Score
            </ScoreBreakdownLabelCell>
          </tr>
        </tbody>
      </table>,
    );

    expect(screen.getByRole('cell').textContent).toBe('Total Score');
  });

  test('shows both arrows when told both alliances won', () => {
    render(
      <table>
        <tbody>
          <tr>
            <ScoreBreakdownLabelCell redWon blueWon>
              Tie
            </ScoreBreakdownLabelCell>
          </tr>
        </tbody>
      </table>,
    );

    expect(screen.getAllByRole('img')).toHaveLength(2);
  });
});
