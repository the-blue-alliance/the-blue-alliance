import { render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import type { QueueResponse } from '~/api/tba/moderation/types.gen';
import {
  SuggestionReviewCard,
  pendingSuggestionTotal,
} from '~/components/tba/account/suggestionReviewCard';

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children?: ReactNode;
    to: string;
  }) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

const QUEUE: QueueResponse = {
  counts: { media: 3, 'social-media': 0, 'offseason-event': 2 },
  type_names: {
    media: 'Team Media',
    'social-media': 'Social Media',
    'offseason-event': 'Offseason Events',
  },
};

describe('pendingSuggestionTotal', () => {
  test('sums every type the moderator can review', () => {
    expect(pendingSuggestionTotal(QUEUE)).toBe(5);
    expect(pendingSuggestionTotal({ counts: {}, type_names: {} })).toBe(0);
  });
});

describe('SuggestionReviewCard', () => {
  test('links moderators to the review home with the pending total', () => {
    render(<SuggestionReviewCard queue={QUEUE} />);

    expect(screen.getByText('Suggestion Reviews')).toBeTruthy();
    expect(screen.getByTestId('pending-suggestions-total').textContent).toBe(
      '5',
    );
    const link = screen.getByRole('link', {
      name: 'Review Pending Suggestions',
    });
    expect(link.getAttribute('href')).toBe('/suggest/review');
  });
});
