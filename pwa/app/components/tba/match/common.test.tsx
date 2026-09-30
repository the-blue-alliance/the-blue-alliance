import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  ConditionalBadge,
  ConditionalCheckmark,
  ConditionalRpAchieved,
  FoulDisplay,
  fmtFouls,
} from '~/components/tba/match/common';

vi.mock('~icons/mdi/check', () => ({
  default: () => <img alt="Achieved" />,
}));

vi.mock('~icons/mdi/close', () => ({
  default: () => <img alt="Not achieved" />,
}));

describe('ConditionalCheckmark', () => {
  test('shows a checkmark when the condition holds', () => {
    render(<ConditionalCheckmark condition={true} teamKey="frc254" />);

    expect(screen.getByRole('img', { name: 'Achieved' })).toBeTruthy();
  });

  test('shows a cross when the condition fails', () => {
    render(<ConditionalCheckmark condition={false} teamKey="frc254" />);

    expect(screen.getByRole('img', { name: 'Not achieved' })).toBeTruthy();
  });

  test('reveals the team number in a tooltip on hover', async () => {
    render(<ConditionalCheckmark condition={true} teamKey="frc254" />);

    const trigger = screen.getByRole('button');
    fireEvent.pointerEnter(trigger);
    fireEvent.mouseEnter(trigger);

    await waitFor(() => {
      expect(screen.getByText('254')).toBeTruthy();
    });
  });
});

describe('ConditionalRpAchieved', () => {
  test('shows a checkmark when the ranking point was achieved', () => {
    render(<ConditionalRpAchieved condition={true} />);

    expect(screen.getByRole('img', { name: 'Achieved' })).toBeTruthy();
  });

  test('shows a cross when the ranking point was not achieved', () => {
    render(<ConditionalRpAchieved condition={false} />);

    expect(screen.getByRole('img', { name: 'Not achieved' })).toBeTruthy();
  });
});

describe('ConditionalBadge', () => {
  test('shows the team number without the frc prefix', () => {
    render(
      <ConditionalBadge condition={true} teamKey="frc1678" alignIcon="left" />,
    );

    expect(screen.getByText('1678')).toBeTruthy();
  });

  test.each([
    { name: 'left', alignIcon: 'left' as const },
    { name: 'right', alignIcon: 'right' as const },
  ])(
    'shows a checkmark when the condition holds with the icon on the $name',
    ({ alignIcon }) => {
      render(
        <ConditionalBadge
          condition={true}
          teamKey="frc1678"
          alignIcon={alignIcon}
        />,
      );

      expect(screen.getByRole('img', { name: 'Achieved' })).toBeTruthy();
    },
  );

  test.each([
    { name: 'left', alignIcon: 'left' as const },
    { name: 'right', alignIcon: 'right' as const },
  ])(
    'shows a cross when the condition fails with the icon on the $name',
    ({ alignIcon }) => {
      render(
        <ConditionalBadge
          condition={false}
          teamKey="frc1678"
          alignIcon={alignIcon}
        />,
      );

      expect(screen.getByRole('img', { name: 'Not achieved' })).toBeTruthy();
    },
  );

  test('renders exactly one icon', () => {
    render(
      <ConditionalBadge condition={true} teamKey="frc1678" alignIcon="right" />,
    );

    expect(screen.getAllByRole('img')).toHaveLength(1);
  });
});

describe('fmtFouls', () => {
  test('multiplies the foul count by the points per foul', () => {
    expect(fmtFouls({ foulCount: 3, pointsPerFoul: 5 })).toBe('3 (+15)');
  });

  test('treats a missing foul count as zero', () => {
    expect(fmtFouls({ foulCount: undefined, pointsPerFoul: 5 })).toBe('0 (+0)');
  });
});

describe('FoulDisplay', () => {
  test('shows regular foul count and points', () => {
    render(
      <FoulDisplay
        foulsReceived={2}
        pointsPerFoul={5}
        techFoulsReceived={1}
        pointsPerTechFoul={25}
        techOrMajor="tech"
      />,
    );

    expect(screen.getByText('2 (+10)')).toBeTruthy();
  });

  test('labels the second line Tech for tech fouls', () => {
    render(
      <FoulDisplay
        foulsReceived={2}
        pointsPerFoul={5}
        techFoulsReceived={1}
        pointsPerTechFoul={25}
        techOrMajor="tech"
      />,
    );

    expect(screen.getByText('Tech:')).toBeTruthy();
  });

  test('labels the second line Major for major fouls', () => {
    render(
      <FoulDisplay
        foulsReceived={2}
        pointsPerFoul={2}
        techFoulsReceived={1}
        pointsPerTechFoul={6}
        techOrMajor="major"
      />,
    );

    expect(screen.getByText('Major:')).toBeTruthy();
  });

  test('shows tech foul count and points', () => {
    render(
      <FoulDisplay
        foulsReceived={2}
        pointsPerFoul={5}
        techFoulsReceived={1}
        pointsPerTechFoul={25}
        techOrMajor="tech"
      />,
    );

    expect(screen.getByText('1 (+25)')).toBeTruthy();
  });

  test('shows zero fouls when counts are missing', () => {
    render(
      <FoulDisplay
        foulsReceived={undefined}
        pointsPerFoul={5}
        techFoulsReceived={undefined}
        pointsPerTechFoul={25}
        techOrMajor="tech"
      />,
    );

    expect(screen.getAllByText('0 (+0)')).toHaveLength(2);
  });
});
