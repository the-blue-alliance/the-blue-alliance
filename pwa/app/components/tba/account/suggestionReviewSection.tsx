import type { JSX } from 'react';

import { SuggestionReviewCard } from '~/components/tba/account/suggestionReviewCard';
import { useModerationQueue } from '~/lib/hooks/useModeration';

// Shown only to moderators. The queue endpoint 403s for everyone else, so a
// failed request simply means there is nothing to show.
export function SuggestionReviewSection(): JSX.Element | null {
  const { data, error } = useModerationQueue();
  if (error || !data) {
    return null;
  }
  return <SuggestionReviewCard queue={data} />;
}
