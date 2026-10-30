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
    autoPoints: 20,
    teleopPoints: 90,
    containerPoints: 48,
    totePoints: 24,
    litterPoints: 18,
    foulPoints: 6,
    adjustPoints: 0,
    totalPoints: 116,
    foulCount: 1,
    toteCountFar: 6,
    toteCountNear: 6,
    toteSet: true,
    toteStack: false,
    containerCountLevel1: 0,
    containerCountLevel2: 0,
    containerCountLevel3: 0,
    containerCountLevel4: 3,
    containerCountLevel5: 0,
    containerCountLevel6: 3,
    containerSet: true,
    litterCountContainer: 3,
    litterCountLandfill: 4,
    litterCountUnprocessed: 2,
    robotSet: true,
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
  };
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
    { label: 'Robot Set', field: 'robotSet' as const, points: '4' },
    { label: 'Container Set', field: 'containerSet' as const, points: '8' },
    { label: 'Tote Set', field: 'toteSet' as const, points: '6' },
    { label: 'Stacked Tote Set', field: 'toteStack' as const, points: '20' },
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
          { robotSet: undefined },
          { robotSet: undefined },
        )}
      />,
    );

    expect(rowCells('Robot Set')).toEqual(['0', 'Robot Set', '0']);
  });

  test.each([
    { label: 'Total Auto', field: 'autoPoints' as const },
    { label: 'Tote Points', field: 'totePoints' as const },
    { label: 'Container Points', field: 'containerPoints' as const },
    { label: 'Litter Points', field: 'litterPoints' as const },
    { label: 'Total Teleop', field: 'teleopPoints' as const },
    { label: 'Foul Points', field: 'foulPoints' as const },
    { label: 'Total Score', field: 'totalPoints' as const },
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
          { totalPoints: 100 },
          { totalPoints: 140 },
        )}
      />,
    );

    const row = screen.getByText('Total Score').closest('tr');
    expect(
      within(row as HTMLElement).getByRole('img', { name: 'Blue leads' }),
    ).toBeTruthy();
  });

  test.each([
    { label: 'Total Auto', field: 'autoPoints' as const },
    { label: 'Tote Points', field: 'totePoints' as const },
    { label: 'Container Points', field: 'containerPoints' as const },
    { label: 'Litter Points', field: 'litterPoints' as const },
    { label: 'Total Teleop', field: 'teleopPoints' as const },
    { label: 'Foul Points', field: 'foulPoints' as const },
    { label: 'Total Score', field: 'totalPoints' as const },
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
