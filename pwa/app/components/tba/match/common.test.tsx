import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  ConditionalBadge,
  ConditionalCheckmark,
  ConditionalRpAchieved,
  fmtFoulsCommitted,
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

  test('renders without a team key', () => {
    render(<ConditionalBadge condition={true} alignIcon="left" />);

    expect(screen.getAllByRole('img')).toHaveLength(1);
  });
});

describe('fmtFoulsCommitted', () => {
  test('shows plain fouls and tech fouls committed', () => {
    expect(fmtFoulsCommitted({ fouls: 3, techFouls: 1 })).toBe('3 / 1');
  });

  test('treats missing counts as zero', () => {
    expect(fmtFoulsCommitted({ fouls: undefined, techFouls: undefined })).toBe(
      '0 / 0',
    );
  });
});
