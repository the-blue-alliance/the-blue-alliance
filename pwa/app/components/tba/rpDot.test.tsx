import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import RpDots from '~/components/tba/rpDot';
import { TooltipProvider } from '~/components/ui/tooltip';

describe('RpDots', () => {
  test('renders RP dots in a single trigger and opens combined tooltip on hover', async () => {
    const scoreBreakdown = {
      autoBonusAchieved: true,
      coralBonusAchieved: true,
      bargeBonusAchieved: false,
    };

    const { container } = render(
      <TooltipProvider delay={0}>
        <RpDots score_breakdown={scoreBreakdown as any} year={2025} />
      </TooltipProvider>,
    );

    const trigger = container.querySelector('button');
    expect(trigger).toBeTruthy();
    expect(trigger?.getAttribute('aria-label')).toBe(
      'Auto Bonus (Achieved), Coral Bonus (Achieved), Barge Bonus (Not Achieved)',
    );

    const svgs = trigger?.querySelectorAll('svg');
    expect(svgs?.length).toBe(3);

    // Hover trigger
    fireEvent.pointerEnter(trigger!);
    fireEvent.mouseEnter(trigger!);

    await waitFor(() => {
      expect(screen.getByText('Auto Bonus')).toBeTruthy();
      expect(screen.getByText('Coral Bonus')).toBeTruthy();
      expect(screen.getByText('Barge Bonus')).toBeTruthy();
    });
  });

  test('opens combined tooltip on keyboard focus', async () => {
    const scoreBreakdown = {
      autoBonusAchieved: true,
      coralBonusAchieved: true,
      bargeBonusAchieved: false,
    };

    const { container } = render(
      <TooltipProvider delay={0}>
        <RpDots score_breakdown={scoreBreakdown as any} year={2025} />
      </TooltipProvider>,
    );

    const trigger = container.querySelector('button');
    fireEvent.focus(trigger!);

    await waitFor(() => {
      expect(screen.getByText('Auto Bonus')).toBeTruthy();
      expect(screen.getByText('Coral Bonus')).toBeTruthy();
      expect(screen.getByText('Barge Bonus')).toBeTruthy();
    });
  });

  test('falls back gracefully when year is unknown in ranking point labels', async () => {
    const scoreBreakdown = {
      autoBonusAchieved: true,
      coralBonusAchieved: false,
      bargeBonusAchieved: false,
    };

    const { container } = render(
      <TooltipProvider delay={0}>
        <RpDots score_breakdown={scoreBreakdown as any} year={1999} />
      </TooltipProvider>,
    );

    const trigger = container.querySelector('button');
    expect(trigger).toBeTruthy();
    expect(trigger?.getAttribute('aria-label')).toBe(
      'Ranking Point (Achieved), Ranking Point (Not Achieved), Ranking Point (Not Achieved)',
    );
  });

  test('renders nothing when score breakdown has no bonus ranking points', () => {
    const { container } = render(
      <TooltipProvider delay={0}>
        <RpDots score_breakdown={{} as any} year={2025} />
      </TooltipProvider>,
    );

    expect(container.firstChild).toBeNull();
  });
});
