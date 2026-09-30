import { fireEvent, render, screen, within } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import type { InsightV2Streak, InsightV2StreakData } from '~/api/tba/read';
import { StreakInsight } from '~/components/tba/streakInsight';

vi.mock('~/components/tba/links', () => ({
  TeamLink: ({
    children,
    teamOrKey,
    year,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement> & {
    children?: ReactNode;
    teamOrKey: string;
    year: number;
  }) => (
    <a href={`/team/${teamOrKey}/${year}`} {...props}>
      {children}
    </a>
  ),
  EventLink: ({
    children,
    eventOrKey,
  }: {
    children?: ReactNode;
    eventOrKey: string;
  }) => <a href={`/event/${eventOrKey}`}>{children}</a>,
}));

type Entry = InsightV2StreakData['entries'][number];

function entry(overrides: Partial<Entry>): Entry {
  return {
    key: 'frc254',
    key_type: 'team',
    streak_length: 5,
    start: '2020',
    end: '2024',
    is_active: false,
    ...overrides,
  };
}

function streak(entries: Entry[]): InsightV2Streak {
  return {
    name: 'win_streak',
    display_name: 'Winning Streaks',
    year: 0,
    category: 'streak',
    district_abbreviation: null,
    data: { entries },
  };
}

describe('StreakInsight', () => {
  test('renders team, event, and match streaks with ranges', () => {
    render(
      <StreakInsight
        subtitle="All time"
        streak={streak([
          entry({ is_active: true }),
          entry({
            key: '2024casj',
            key_type: 'event',
            start: '2024casj',
            end: '2024casj',
          }),
          entry({
            key: '2024casj_qm1',
            key_type: 'match',
            start: '2023casj',
            end: '2024casj',
          }),
        ])}
      />,
    );
    const rows = screen.getAllByRole('row').slice(1);

    expect(rows[0].textContent).toBe('5254' + '2020 – 2024Active');
    expect(
      within(rows[0]).getByRole('link', { name: '254' }).getAttribute('href'),
    ).toBe('/team/frc254/0');

    expect(rows[1].textContent).toBe('52024casj2024casj – (same)');
    expect(within(rows[1]).getAllByRole('link')).toHaveLength(2);

    expect(rows[2].textContent).toBe('52024casj_qm12023casj – 2024casj');
    expect(
      within(rows[2])
        .getAllByRole('link')
        .map((l) => l.getAttribute('href')),
    ).toEqual(['/event/2023casj', '/event/2024casj']);
  });

  test('shows ten rows until expanded', () => {
    render(
      <StreakInsight
        streak={streak(
          Array.from({ length: 12 }, (_, i) =>
            entry({ key: `frc${i + 1}`, start: String(2000 + i) }),
          ),
        )}
      />,
    );
    expect(screen.getAllByRole('row')).toHaveLength(11);
    fireEvent.click(screen.getByRole('button', { name: 'Toggle' }));
    expect(screen.getAllByRole('row')).toHaveLength(13);
  });
});
