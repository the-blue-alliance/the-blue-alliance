import { render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { CompLevel, type Event, type Match } from '~/api/tba/read';
import EventPracticeTab from '~/components/tba/eventPracticeTab';

vi.mock('~/components/tba/match/matchRows', () => ({
  default: ({ matches }: { matches: Match[] }) => (
    <ul aria-label="Matches">
      {matches.map((m) => (
        <li key={m.key}>{m.key}</li>
      ))}
    </ul>
  ),
}));

const event = { key: '2026nysu', year: 2026 } as Event;

function practiceMatch(matchNumber: number): Match {
  return {
    key: `2026nysu_pm${matchNumber}`,
    comp_level: CompLevel.PM,
    set_number: 1,
    match_number: matchNumber,
  } as Match;
}

describe('EventPracticeTab', () => {
  test('shows the practice matches heading', () => {
    render(<EventPracticeTab event={event} matches={[practiceMatch(1)]} />);

    expect(
      screen.getByRole('heading', { name: 'Practice Matches' }),
    ).toBeTruthy();
  });

  test('notes that practice match results are not published', () => {
    render(<EventPracticeTab event={event} matches={[practiceMatch(1)]} />);

    expect(screen.getByRole('note').textContent).toBe(
      'Results are not published for practice matches.',
    );
  });

  test('lists practice matches in match number order', () => {
    render(
      <EventPracticeTab
        event={event}
        matches={[practiceMatch(10), practiceMatch(2)]}
      />,
    );

    expect(
      within(screen.getByRole('list', { name: 'Matches' }))
        .getAllByRole('listitem')
        .map((li) => li.textContent),
    ).toEqual(['2026nysu_pm2', '2026nysu_pm10']);
  });
});
