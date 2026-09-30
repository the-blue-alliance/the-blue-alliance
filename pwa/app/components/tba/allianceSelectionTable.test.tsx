import { render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  CompLevel,
  type EliminationAlliance,
  PlayoffType,
} from '~/api/tba/read';
import AllianceSelectionTable from '~/components/tba/allianceSelectionTable';

vi.mock('~/components/tba/teamTooltip', () => ({
  TeamLinkWithTooltip: ({ teamKey }: { teamKey: string }) => (
    <a href={`/team/${teamKey}`}>{teamKey.substring(3)}</a>
  ),
}));

function alliance(
  overrides: Partial<EliminationAlliance>,
): EliminationAlliance {
  return { declines: [], picks: [], ...overrides };
}

function status(
  level: CompLevel,
  result: 'eliminated' | 'playing' | 'won',
): EliminationAlliance['status'] {
  return {
    playoff_type: PlayoffType.DOUBLE_ELIM_8_TEAM,
    level,
    record: null,
    current_level_record: null,
    status: result,
  };
}

function headers() {
  return screen.getAllByRole('columnheader').map((h) => h.textContent);
}

describe('AllianceSelectionTable', () => {
  test('renders alliances with winners, finalists, and missing picks', () => {
    render(
      <AllianceSelectionTable
        year={2026}
        alliances={[
          alliance({
            name: 'Alliance 1',
            picks: ['frc254', 'frc604', 'frc1678', 'frc4414'],
            status: status(CompLevel.F, 'won'),
          }),
          alliance({
            name: 'Alliance 2',
            picks: ['frc1', 'frc2', 'frc3'],
            status: status(CompLevel.F, 'eliminated'),
          }),
          alliance({
            name: 'Custom Name',
            picks: ['frc4', 'frc5'],
            status: status(CompLevel.SF, 'eliminated'),
          }),
          alliance({ picks: ['frc6'] }),
        ]}
      />,
    );
    expect(headers()).toEqual([
      'Alliance',
      'Captain',
      'Pick 1',
      'Pick 2',
      'Pick 3',
    ]);
    const [, winner, finalist, other, unnamed] = screen.getAllByRole('row');
    expect(winner.className).toContain('bg-yellow-100!');
    expect(winner.querySelector('svg')).toBeTruthy();
    expect(within(winner).getAllByRole('cell')[0].textContent).toBe('1');
    expect(finalist.className).toContain('bg-neutral-100!');
    expect(
      within(other)
        .getAllByRole('cell')
        .map((c) => c.textContent),
    ).toEqual(['Custom Name', '4', '5', '-', '-']);
    expect(other.className).not.toContain('!');
    expect(
      within(unnamed)
        .getAllByRole('cell')
        .map((c) => c.textContent),
    ).toEqual(['4', '6', '-', '-', '-']);
  });

  test('uses three columns when no alliance has picks', () => {
    render(<AllianceSelectionTable year={2026} alliances={[alliance({})]} />);
    expect(headers()).toEqual(['Alliance', 'Captain', 'Pick 1', 'Pick 2']);
  });

  test('Bug #64: an empty alliance list falls back to the default three team columns', () => {
    // Wrong today: Math.max() of nothing is -Infinity, which is truthy, so
    // the `|| 3` fallback never applies and only Alliance and Captain render.
    // Correct: the fallback applies, giving the same Captain, Pick 1, Pick 2
    // columns as a list whose alliances have no picks.
    render(<AllianceSelectionTable year={2026} alliances={[]} />);
    expect(headers()).toEqual(['Alliance', 'Captain', 'Pick 1', 'Pick 2']);
  });

  test('renders a single-team alliance without pick columns', () => {
    render(
      <AllianceSelectionTable
        year={2026}
        alliances={[alliance({ name: 'Alliance 1', picks: ['frc254'] })]}
      />,
    );
    expect(headers()).toEqual(['Alliance', 'Captain']);
  });
});
