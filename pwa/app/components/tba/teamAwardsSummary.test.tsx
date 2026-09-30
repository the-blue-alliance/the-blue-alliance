import { render, screen, within } from '@testing-library/react';
import { type ReactElement, type ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import { type Award, AwardType, type Event } from '~/api/tba/read';
import TeamAwardsSummary from '~/components/tba/teamAwardsSummary';

vi.mock('~/components/tba/links', () => ({
  EventLink: ({
    children,
    eventOrKey,
  }: {
    children: ReactNode;
    eventOrKey: string;
  }) => <a href={`/event/${eventOrKey}`}>{children}</a>,
}));

// Base UI tooltips only open on pointer hover; render the trigger element
// and the content inline so the event list is inspectable.
vi.mock('~/components/ui/tooltip', () => ({
  TooltipProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
  Tooltip: ({ children }: { children: ReactNode }) => (
    <div data-testid="tooltip">{children}</div>
  ),
  TooltipTrigger: ({ render }: { render: ReactElement }) => render,
  TooltipContent: ({ children }: { children: ReactNode }) => (
    <div data-testid="tooltip-content">{children}</div>
  ),
}));

function makeAward(
  award_type: AwardType,
  event_key: string,
  name = 'Award',
): Award {
  return {
    name,
    award_type,
    event_key,
    recipient_list: [{ team_key: 'frc254', awardee: null }],
    year: Number(event_key.substring(0, 4)),
  };
}

const events = [
  {
    key: '2025casj',
    year: 2025,
    name: 'Silicon Valley Regional',
    short_name: 'Silicon Valley',
  },
  {
    key: '2024casf',
    year: 2024,
    name: 'San Francisco Regional',
    short_name: null,
  },
  {
    key: '2023cada',
    year: 2023,
    name: 'Sacramento Regional',
    short_name: '  ',
  },
] as Event[];

function itemRow(label: string) {
  const checkbox = screen
    .getAllByRole('checkbox')
    .find((c) => c.getAttribute('aria-label') === label);
  const row = checkbox?.closest('label');
  if (!row) throw new Error(`no row for ${label}`);
  return row;
}

describe('TeamAwardsSummary', () => {
  test('renders nothing when there are no awards', () => {
    const { container } = render(
      <TeamAwardsSummary awards={[]} events={events} />,
    );
    expect(container.innerHTML).toBe('');
  });

  test('shows the award and banner totals', () => {
    render(
      <TeamAwardsSummary
        awards={[
          makeAward(AwardType.CHAIRMANS, '2025casj'),
          makeAward(AwardType.WINNER, '2024casf'),
          makeAward(AwardType.QUALITY, '2024casf'),
        ]}
        events={events}
      />,
    );

    expect(screen.getByText('Awards Won')).toBeTruthy();
    expect(screen.getByText('(3)')).toBeTruthy();
    expect(screen.getByText('(2 banners)')).toBeTruthy();
  });

  test('uses the singular for one banner and hides the banner count with none', () => {
    const { unmount } = render(
      <TeamAwardsSummary
        awards={[makeAward(AwardType.WINNER, '2024casf')]}
        events={events}
      />,
    );
    expect(screen.getByText('(1 banner)')).toBeTruthy();
    unmount();

    render(
      <TeamAwardsSummary
        awards={[makeAward(AwardType.QUALITY, '2024casf')]}
        events={events}
      />,
    );
    expect(screen.queryByText(/banner/)).toBeNull();
  });

  test('lists every category with its items sorted alphabetically', () => {
    render(
      <TeamAwardsSummary
        awards={[makeAward(AwardType.QUALITY, '2024casf')]}
        events={events}
      />,
    );

    for (const title of [
      'Team awards',
      'Robot awards',
      'Individual awards',
      'Performance',
      'Rookie',
      'Other',
    ]) {
      expect(screen.getByText(title)).toBeTruthy();
    }

    const labels = screen
      .getAllByRole('checkbox')
      .map((c) => c.getAttribute('aria-label'));
    expect(labels.slice(5, 11)).toEqual([
      'Auto',
      'Creativity',
      'Engineering Excellence',
      'Industrial Design',
      'Innovation in Control',
      'Quality',
    ]);
  });

  test('counts awards per category and per item', () => {
    render(
      <TeamAwardsSummary
        awards={[
          makeAward(AwardType.CHAIRMANS, '2025casj'),
          makeAward(AwardType.CHAIRMANS_FINALIST, '2024casf'),
          makeAward(AwardType.WINNER, '2024casf'),
          // Not in any category: only counts toward the header total.
          makeAward(AwardType.HIGHEST_ROOKIE_SEED, '2024casf'),
        ]}
        events={events}
      />,
    );

    expect(screen.getByText('(4)')).toBeTruthy();
    const teamTitle = screen.getByText('Team awards');
    expect(teamTitle.textContent).toBe('Team awards(2)');
    expect(screen.getByText('Performance').textContent).toBe('Performance(1)');
    expect(screen.getByText('Rookie').textContent).toBe('Rookie');

    const impact = itemRow('Impact');
    expect(within(impact).getByText('2')).toBeTruthy();
    expect(
      within(impact).getByRole('checkbox').getAttribute('aria-checked'),
    ).toBe('true');
    expect(within(impact).getByText('Impact').className).toContain(
      'font-medium',
    );

    const finalist = itemRow('Finalist');
    expect(within(finalist).getByText('0')).toBeTruthy();
    expect(
      within(finalist).getByRole('checkbox').getAttribute('aria-checked'),
    ).toBe('false');
    expect(within(finalist).getByText('Finalist').className).toContain(
      'text-muted-foreground',
    );
  });

  test('links each event an award was won at, once, using the short name when set', () => {
    render(
      <TeamAwardsSummary
        awards={[
          makeAward(AwardType.WINNER, '2025casj'),
          makeAward(AwardType.WINNER, '2025casj'),
          makeAward(AwardType.WINNER, '2024casf'),
          makeAward(AwardType.WINNER, '2023cada'),
          makeAward(AwardType.WINNER, '2022unknown'),
        ]}
        events={events}
      />,
    );

    const content = screen.getByTestId('tooltip-content');
    const links = within(content).getAllByRole('link');
    expect(links.map((l) => l.textContent)).toEqual([
      '2025 Silicon Valley',
      '2024 San Francisco Regional',
      '2023 Sacramento Regional',
      '2022unknown',
    ]);
    expect(links[0].getAttribute('href')).toBe('/event/2025casj');
  });

  test('skips the tooltip for items without awards or without event keys', () => {
    render(
      <TeamAwardsSummary
        awards={[makeAward(AwardType.SPIRIT, '')]}
        events={events}
      />,
    );

    expect(screen.queryByTestId('tooltip')).toBeNull();
    const spirit = itemRow('Spirit');
    expect(within(spirit).getByText('1')).toBeTruthy();
  });
});
