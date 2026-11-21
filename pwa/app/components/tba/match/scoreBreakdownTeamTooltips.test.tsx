import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import {
  AutoLineRobot2024,
  type Match,
  type MatchScoreBreakdown2023,
  type MatchScoreBreakdown2024,
  MobilityRobot2023,
} from '~/api/tba/read';
import ScoreBreakdown2023 from '~/components/tba/match/scoreBreakdown2023';
import ScoreBreakdown2024 from '~/components/tba/match/scoreBreakdown2024';
import { makeMatch as baseMatch, makeAlliance } from '~/test/factories';

function makeMatch(year: number): Match {
  return baseMatch({
    key: `${year}test_qm1`,
    alliances: {
      red: makeAlliance(0, ['frc254', 'frc1114', 'frc2056']),
      blue: makeAlliance(0, ['frc148', 'frc217', 'frc33']),
    },
    event_key: `${year}test`,
  });
}

async function hoverFirstCheckmark(row: HTMLElement): Promise<HTMLElement> {
  const trigger = within(row).getAllByRole('button')[0];
  fireEvent.pointerEnter(trigger);
  fireEvent.mouseEnter(trigger);
  return await waitFor(() => {
    const tooltip = document.querySelector<HTMLElement>(
      '[data-slot="tooltip-content"]',
    );
    expect(tooltip).not.toBeNull();
    return tooltip!;
  });
}

// Renders the real ConditionalCheckmark, which the per-year test files mock.
describe('ConditionalCheckmark team tooltips', () => {
  test('2023 mobility tooltip shows the team number', async () => {
    const alliance = { mobilityRobot1: MobilityRobot2023.YES };
    render(
      <ScoreBreakdown2023
        scoreBreakdown={
          {
            red: alliance,
            blue: alliance,
          } as unknown as MatchScoreBreakdown2023
        }
        match={makeMatch(2023)}
      />,
    );
    const row = screen.getByText('Mobility').closest('tr')!;
    const tip = await hoverFirstCheckmark(row);
    expect(tip.textContent).toBe('254');
  });

  test('2024 auto leave tooltip shows the team number', async () => {
    const alliance = { autoLineRobot1: AutoLineRobot2024.YES };
    render(
      <ScoreBreakdown2024
        scoreBreakdown={
          {
            red: alliance,
            blue: alliance,
          } as unknown as MatchScoreBreakdown2024
        }
        match={makeMatch(2024)}
      />,
    );
    const row = screen.getByText('Auto Leave').closest('tr')!;
    const tip = await hoverFirstCheckmark(row);
    expect(tip.textContent).toBe('254');
  });
});
