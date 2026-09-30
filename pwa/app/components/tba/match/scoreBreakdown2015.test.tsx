import { render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  MatchScoreBreakdown2015,
  MatchScoreBreakdown2015Alliance,
} from '~/api/tba/read';
import ScoreBreakdown2015 from '~/components/tba/match/scoreBreakdown2015';

vi.mock('~icons/mdi/arrow-left', () => ({
  default: () => <img alt="Red leads" />,
}));

vi.mock('~icons/mdi/arrow-right', () => ({
  default: () => <img alt="Blue leads" />,
}));

function makeAlliance(
  overrides: Partial<MatchScoreBreakdown2015Alliance> = {},
): MatchScoreBreakdown2015Alliance {
  return {
    auto_points: 20,
    teleop_points: 90,
    container_points: 48,
    tote_points: 24,
    litter_points: 18,
    foul_points: 6,
    adjust_points: 0,
    total_points: 116,
    foul_count: 1,
    tote_count_far: 6,
    tote_count_near: 6,
    tote_set: true,
    tote_stack: false,
    container_count_level1: 0,
    container_count_level2: 0,
    container_count_level3: 0,
    container_count_level4: 3,
    container_count_level5: 0,
    container_count_level6: 3,
    container_set: true,
    litter_count_container: 3,
    litter_count_landfill: 4,
    litter_count_unprocessed: 2,
    robot_set: true,
    ...overrides,
  };
}

function makeBreakdown(
  red: Partial<MatchScoreBreakdown2015Alliance> = {},
  blue: Partial<MatchScoreBreakdown2015Alliance> = {},
): MatchScoreBreakdown2015 {
  return {
    red: makeAlliance(red),
    blue: makeAlliance(blue),
    coopertition: 'Stack',
    coopertition_points: 40,
  } as MatchScoreBreakdown2015;
}

function rowCells(label: string): string[] {
  const row = screen.getByText(label).closest('tr');
  if (!row) {
    throw new Error(`No row labelled ${label}`);
  }
  return within(row)
    .getAllByRole('cell')
    .map((cell) => cell.textContent ?? '');
}

describe('ScoreBreakdown2015', () => {
  test.each([
    { label: 'Robot Set', field: 'robot_set' as const, points: '4' },
    { label: 'Container Set', field: 'container_set' as const, points: '8' },
    { label: 'Tote Set', field: 'tote_set' as const, points: '6' },
    { label: 'Stacked Tote Set', field: 'tote_stack' as const, points: '20' },
  ])(
    'awards $points points for $label when achieved and 0 when not',
    ({ label, field, points }) => {
      render(
        <ScoreBreakdown2015
          scoreBreakdown={makeBreakdown({ [field]: true }, { [field]: false })}
        />,
      );

      expect(rowCells(label)).toEqual([points, label, '0']);
    },
  );

  test('treats a missing auto set flag as not achieved', () => {
    render(
      <ScoreBreakdown2015
        scoreBreakdown={makeBreakdown(
          { robot_set: undefined },
          { robot_set: undefined },
        )}
      />,
    );

    expect(rowCells('Robot Set')).toEqual(['0', 'Robot Set', '0']);
  });

  test.each([
    { label: 'Total Auto', field: 'auto_points' as const },
    { label: 'Tote Points', field: 'tote_points' as const },
    { label: 'Container Points', field: 'container_points' as const },
    { label: 'Litter Points', field: 'litter_points' as const },
    { label: 'Total Teleop', field: 'teleop_points' as const },
    { label: 'Foul Points', field: 'foul_points' as const },
    { label: 'Total Score', field: 'total_points' as const },
  ])('shows each alliance value for $label', ({ label, field }) => {
    render(
      <ScoreBreakdown2015
        scoreBreakdown={makeBreakdown({ [field]: 37 }, { [field]: 12 })}
      />,
    );

    expect(rowCells(label)).toEqual(['37', label, '12']);
  });

  test('points the label at the alliance with the higher total', () => {
    render(
      <ScoreBreakdown2015
        scoreBreakdown={makeBreakdown(
          { total_points: 100 },
          { total_points: 140 },
        )}
      />,
    );

    const row = screen.getByText('Total Score').closest('tr');
    expect(
      within(row as HTMLElement).getByRole('img', { name: 'Blue leads' }),
    ).toBeTruthy();
  });

  test.each([
    { label: 'Total Auto', field: 'auto_points' as const },
    { label: 'Tote Points', field: 'tote_points' as const },
    { label: 'Container Points', field: 'container_points' as const },
    { label: 'Litter Points', field: 'litter_points' as const },
    { label: 'Total Teleop', field: 'teleop_points' as const },
    { label: 'Foul Points', field: 'foul_points' as const },
    { label: 'Total Score', field: 'total_points' as const },
  ])(
    'shows no arrow when $label is missing on both sides',
    ({ label, field }) => {
      render(
        <ScoreBreakdown2015
          scoreBreakdown={makeBreakdown(
            { [field]: undefined },
            { [field]: undefined },
          )}
        />,
      );

      const row = screen.getByText(label).closest('tr');
      expect(within(row as HTMLElement).queryByRole('img')).toBeNull();
    },
  );

  test('renders one row per breakdown line', () => {
    render(<ScoreBreakdown2015 scoreBreakdown={makeBreakdown()} />);

    expect(screen.getAllByRole('row')).toHaveLength(11);
  });
});
