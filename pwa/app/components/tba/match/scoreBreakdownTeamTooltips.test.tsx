import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import {
  AllianceColor,
  AutoLineRobot2024,
  CompLevel,
  type Match,
  type MatchScoreBreakdown2023,
  type MatchScoreBreakdown2024,
  MobilityRobot2023,
} from '~/api/tba/read';
import ScoreBreakdown2023 from '~/components/tba/match/scoreBreakdown2023';
import ScoreBreakdown2024 from '~/components/tba/match/scoreBreakdown2024';

function makeMatch(year: number): Match {
  return {
    key: `${year}test_qm1`,
    comp_level: CompLevel.QM,
    set_number: 1,
    match_number: 1,
    alliances: {
      red: {
        score: 0,
        team_keys: ['frc254', 'frc1114', 'frc2056'],
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
      blue: {
        score: 0,
        team_keys: ['frc148', 'frc217', 'frc33'],
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
    },
    winning_alliance: AllianceColor.RED,
    event_key: `${year}test`,
    time: null,
    actual_time: null,
    predicted_time: null,
    post_result_time: null,
    score_breakdown: null,
    videos: [],
  };
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
