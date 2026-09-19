import type { JSX } from 'react';

import { SuggestionReviewCard } from '~/components/tba/account/suggestionReviewCard';
import { useModerationQueue } from '~/lib/hooks/useModeration';

// Shown only to moderators. The queue is `null` for accounts without review
// permissions, and a failed request is not worth a card on the account page.
export function SuggestionReviewSection(): JSX.Element | null {
  const { data, error } = useModerationQueue();
  if (error || !data) {
    return null;
  }
  return <SuggestionReviewCard queue={data} />;
}
