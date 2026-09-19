import { Link } from '@tanstack/react-router';
import type { JSX } from 'react';

import type { QueueResponse } from '~/api/tba/moderation/types.gen';
import { Button } from '~/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';

export function pendingSuggestionTotal(queue: QueueResponse): number {
  return Object.values(queue.counts).reduce(
    (sum: number, count: number) => sum + count,
    0,
  );
}

// Presentational. SuggestionReviewSection on the account page decides
// whether to show it (only moderators get a queue back from the API).
export function SuggestionReviewCard({
  queue,
}: {
  queue: QueueResponse;
}): JSX.Element {
  const total = pendingSuggestionTotal(queue);
  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>Suggestion Reviews</CardTitle>
        <CardDescription>
          Your account has permission to help review community suggestions
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg border bg-card p-4">
          <div
            className="text-2xl font-bold text-foreground"
            data-testid="pending-suggestions-total"
          >
            {total}
          </div>
          <div className="text-sm text-muted-foreground">
            Pending suggestions you can review
          </div>
        </div>
        <Button size="sm" render={<Link to="/suggest/review" />}>
          Review Pending Suggestions
        </Button>
      </CardContent>
    </Card>
  );
}
