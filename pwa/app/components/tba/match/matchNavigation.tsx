import { Link } from '@tanstack/react-router';

import ChevronLeftIcon from '~icons/lucide/chevron-left';
import ChevronRightIcon from '~icons/lucide/chevron-right';

import { type Match, PlayoffType } from '~/api/tba/read';
import LoadingSkeleton from '~/components/tba/loadingSkeleton';
import { buttonVariants } from '~/components/ui/button';
import { adjacentMatches, matchTitleShort } from '~/lib/matchUtils';

export default function MatchNavigation({
  matchKey,
  matches,
  isPending,
  playoffType,
}: {
  matchKey: string;
  matches: Match[] | undefined;
  isPending: boolean;
  playoffType: PlayoffType;
}) {
  if (isPending) {
    return (
      <LoadingSkeleton
        label="Loading adjacent matches"
        className="mb-4 h-9 rounded-md"
      />
    );
  }

  const { previous, next } = adjacentMatches(matches ?? [], matchKey);
  if (!previous && !next) {
    return null;
  }

  return (
    <nav aria-label="Event matches" className="mb-4 flex justify-between gap-2">
      {previous ? (
        <Link
          to="/match/$matchKey"
          params={{ matchKey: previous.key }}
          aria-label={`Previous match: ${matchTitleShort(previous, playoffType)}`}
          className={buttonVariants({ variant: 'outline', size: 'sm' })}
        >
          <ChevronLeftIcon className="mr-1 size-4" />
          {matchTitleShort(previous, playoffType)}
        </Link>
      ) : (
        <span />
      )}
      {next && (
        <Link
          to="/match/$matchKey"
          params={{ matchKey: next.key }}
          aria-label={`Next match: ${matchTitleShort(next, playoffType)}`}
          className={buttonVariants({ variant: 'outline', size: 'sm' })}
        >
          {matchTitleShort(next, playoffType)}
          <ChevronRightIcon className="ml-1 size-4" />
        </Link>
      )}
    </nav>
  );
}
