import { Link, createFileRoute } from '@tanstack/react-router';
import { type JSX } from 'react';

import { SuggestionType } from '~/api/tba/moderation/types.gen';
import { useAuth } from '~/components/tba/auth/auth';
import LoginPage from '~/components/tba/auth/loginPage';
import {
  ReviewMediaTools,
  ReviewOffseasonTools,
} from '~/components/tba/moderation/reviewTools';
import { Badge } from '~/components/ui/badge';
import { Card } from '~/components/ui/card';
import { Spinner } from '~/components/ui/spinner';
import { useModerationQueue } from '~/lib/hooks/useModeration';
import { suggestionTypeOrderComparator } from '~/lib/moderationUtils';

export const Route = createFileRoute('/suggest/review/')({
  component: SuggestionReviewHome,
});

function SuggestionReviewHome(): JSX.Element {
  const { isInitialLoading, user } = useAuth();
  const { data, isLoading, error } = useModerationQueue();

  if (isInitialLoading) {
    return <Spinner className="mx-auto mt-16" />;
  }
  if (!user) {
    return <LoginPage />;
  }
  if (error) {
    return (
      <div className="mx-auto mt-16 max-w-lg text-center">
        <h1 className="text-2xl font-semibold">Suggestion Review</h1>
        <p className="mt-4 text-muted-foreground">
          You do not have permission to review suggestions. If this is
          incorrect, please contact the TBA admins.
        </p>
      </div>
    );
  }
  if (isLoading || !data) {
    return <Spinner className="mx-auto mt-16" />;
  }

  const types = (Object.keys(data.counts) as SuggestionType[]).sort(
    suggestionTypeOrderComparator,
  );

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4 p-4">
      <h1 className="text-2xl font-semibold">Suggestion Review</h1>
      <p className="text-muted-foreground">
        Review pending community suggestions. You can review the following
        suggestion types:
      </p>
      <div className="flex flex-col gap-2">
        {types.map((type) => (
          <Link
            key={type}
            to="/suggest/review/$suggestionType"
            params={{ suggestionType: type }}
            className="text-foreground hover:no-underline"
          >
            <Card
              className="flex items-center justify-between p-4 transition-colors
                hover:bg-accent"
            >
              <span className="font-medium">
                {data.type_names[type] ?? type}
              </span>
              <Badge
                variant={data.counts[type] > 0 ? 'default' : 'secondary'}
                data-testid={`count-${type}`}
              >
                {data.counts[type]} pending
              </Badge>
            </Card>
          </Link>
        ))}
      </div>
      {types.includes(SuggestionType.MEDIA) && <ReviewMediaTools />}
      {types.includes(SuggestionType.OFFSEASON_EVENT) && (
        <ReviewOffseasonTools />
      )}
    </div>
  );
}
