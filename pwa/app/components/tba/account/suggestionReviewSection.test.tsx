import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { SuggestionReviewSection } from '~/components/tba/account/suggestionReviewSection';
import { useModerationQueue } from '~/lib/hooks/useModeration';

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children, to }: { children?: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
}));

vi.mock('~/lib/hooks/useModeration', () => ({
  useModerationQueue: vi.fn<() => unknown>(),
}));

const mockQueue = vi.mocked(useModerationQueue);

describe('SuggestionReviewSection', () => {
  test('shows the card to moderators', () => {
    mockQueue.mockReturnValue({
      data: { counts: { media: 2 }, type_names: { media: 'Team Media' } },
      error: null,
    } as unknown as ReturnType<typeof useModerationQueue>);

    render(<SuggestionReviewSection />);

    expect(screen.getByText('Suggestion Reviews')).toBeTruthy();
    expect(screen.getByTestId('pending-suggestions-total').textContent).toBe(
      '2',
    );
  });

  test('renders nothing for accounts without review permissions', () => {
    mockQueue.mockReturnValue({
      data: null,
      error: null,
    } as unknown as ReturnType<typeof useModerationQueue>);

    const { container } = render(<SuggestionReviewSection />);

    expect(container.innerHTML).toBe('');
  });

  test('renders nothing while loading or when the request fails', () => {
    mockQueue.mockReturnValue({
      data: undefined,
      error: null,
    } as unknown as ReturnType<typeof useModerationQueue>);
    expect(render(<SuggestionReviewSection />).container.innerHTML).toBe('');

    mockQueue.mockReturnValue({
      data: undefined,
      error: new Error('boom'),
    } as unknown as ReturnType<typeof useModerationQueue>);
    expect(render(<SuggestionReviewSection />).container.innerHTML).toBe('');
  });
});
