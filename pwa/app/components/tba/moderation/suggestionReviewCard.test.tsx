import { fireEvent, render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import type {
  AcceptRequest,
  ModerationSuggestion,
} from '~/api/tba/moderation/types.gen';
import { SuggestionType } from '~/api/tba/moderation/types.gen';
import { EventType } from '~/api/tba/read';
import { SuggestionReviewCard } from '~/components/tba/moderation/suggestionReviewCard';

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    params,
    to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children: ReactNode;
    params?: Record<string, string>;
    to: string;
  }) => (
    <a
      href={Object.entries(params ?? {}).reduce(
        (href, [key, value]) => href.replace(`$${key}`, value),
        to,
      )}
      {...props}
    >
      {children}
    </a>
  ),
}));

const OFFSEASON_SUGGESTION = {
  key: 'offseason-1',
  target_model: SuggestionType.OFFSEASON_EVENT,
  contents: {
    name: 'Chezy Champs',
    start_date: '2026-09-25',
    end_date: '2026-09-27',
    venue_name: 'Bellarmine College Preparatory',
    address: '960 W Hedding St',
    city: 'San Jose',
    state: 'CA',
    country: 'USA',
    website: 'https://cheesyarena.com',
  },
} as unknown as ModerationSuggestion;

describe('SuggestionReviewCard offseason event', () => {
  test('defaults the event type select to Offseason, matching the API', () => {
    render(
      <SuggestionReviewCard
        suggestion={OFFSEASON_SUGGESTION}
        decision={undefined}
        onDecisionChange={() => {}}
        overrides={{}}
        onOverridesChange={() => {}}
      />,
    );

    const select = screen.getByLabelText('Event type') as HTMLSelectElement;
    expect(Number(select.value)).toBe(EventType.OFFSEASON);
    expect(
      Array.from(select.options).map((option) => option.textContent),
    ).toEqual(['Offseason', 'Preseason']);
  });

  test('choosing Preseason sends event_type_enum as a number', () => {
    const onOverridesChange = vi.fn<(overrides: AcceptRequest) => void>();
    render(
      <SuggestionReviewCard
        suggestion={OFFSEASON_SUGGESTION}
        decision={undefined}
        onDecisionChange={() => {}}
        overrides={{ event_short: 'cc' }}
        onOverridesChange={onOverridesChange}
      />,
    );

    fireEvent.change(screen.getByLabelText('Event type'), {
      target: { value: String(EventType.PRESEASON) },
    });

    expect(onOverridesChange).toHaveBeenCalledWith({
      event_short: 'cc',
      event_type_enum: EventType.PRESEASON,
    });
  });

  test('shows the moderator override once chosen', () => {
    render(
      <SuggestionReviewCard
        suggestion={OFFSEASON_SUGGESTION}
        decision={undefined}
        onDecisionChange={() => {}}
        overrides={{ event_type_enum: EventType.PRESEASON }}
        onOverridesChange={() => {}}
      />,
    );

    const select = screen.getByLabelText('Event type') as HTMLSelectElement;
    expect(Number(select.value)).toBe(EventType.PRESEASON);
  });
});
