import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { CompLevel, MatchScoreBreakdown2019Alliance } from '~/api/tba/read';
import ScoreCell from '~/components/tba/match/scoreCell';
import { TooltipProvider } from '~/components/ui/tooltip';

const breakdown2019 = {
  completeRocketRankingPoint: true,
  habDockingRankingPoint: false,
} as MatchScoreBreakdown2019Alliance;

describe('ScoreCell', () => {
  test('shows the score', () => {
    render(<ScoreCell score={87} compLevel={CompLevel.F} />);

    expect(screen.getByText('87')).toBeTruthy();
  });

  test('shows ranking point dots for a qualification match with a breakdown', () => {
    render(
      <TooltipProvider>
        <ScoreCell
          score={87}
          compLevel={CompLevel.QM}
          scoreBreakdown={breakdown2019}
          year={2019}
        />
      </TooltipProvider>,
    );

    expect(
      screen.getByRole('button', {
        name: 'Complete Rocket (Achieved), Hab Docking (Not Achieved)',
      }),
    ).toBeTruthy();
  });

  test('hides ranking point dots for a playoff match', () => {
    render(
      <TooltipProvider>
        <ScoreCell
          score={87}
          compLevel={CompLevel.SF}
          scoreBreakdown={breakdown2019}
          year={2019}
        />
      </TooltipProvider>,
    );

    expect(screen.queryByRole('button')).toBeNull();
  });

  test('hides ranking point dots when there is no breakdown', () => {
    render(
      <TooltipProvider>
        <ScoreCell score={87} compLevel={CompLevel.QM} year={2019} />
      </TooltipProvider>,
    );

    expect(screen.queryByRole('button')).toBeNull();
  });

  test('hides ranking point dots when the year is unknown', () => {
    render(
      <TooltipProvider>
        <ScoreCell
          score={87}
          compLevel={CompLevel.QM}
          scoreBreakdown={breakdown2019}
        />
      </TooltipProvider>,
    );

    expect(screen.queryByRole('button')).toBeNull();
  });

  test('shows the score for the winning alliance', () => {
    render(
      <ScoreCell
        score={112}
        compLevel={CompLevel.QM}
        winner
        allianceColor="red"
      />,
    );

    expect(screen.getByText('112')).toBeTruthy();
  });

  test('shows the score for a focused losing alliance', () => {
    render(
      <ScoreCell
        score={64}
        compLevel={CompLevel.QM}
        winner={false}
        allianceColor="blue"
        focused
      />,
    );

    expect(screen.getByText('64')).toBeTruthy();
  });
});
