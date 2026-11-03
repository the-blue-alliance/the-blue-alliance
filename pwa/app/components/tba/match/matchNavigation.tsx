import { Link } from '@tanstack/react-router';

import ChevronLeftIcon from '~icons/lucide/chevron-left';
import ChevronRightIcon from '~icons/lucide/chevron-right';

import { type Match, PlayoffType } from '~/api/tba/read';
import LoadingSkeleton from '~/components/tba/loadingSkeleton';
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
        className="h-6 w-48 rounded-md"
      />
    );
  }

  const { previous, next } = adjacentMatches(matches ?? [], matchKey);
  if (!previous && !next) {
    return null;
  }

  return (
    <nav aria-label="Event matches" className="flex gap-4">
      {previous && (
        <Link
          to="/match/$matchKey"
          params={{ matchKey: previous.key }}
          aria-label={`Previous match: ${matchTitleShort(previous, playoffType)}`}
          className="whitespace-nowrap"
        >
          <ChevronLeftIcon className="inline size-4 align-[-0.2em]" />
          {matchTitleShort(previous, playoffType)}
        </Link>
      )}
      {next && (
        <Link
          to="/match/$matchKey"
          params={{ matchKey: next.key }}
          aria-label={`Next match: ${matchTitleShort(next, playoffType)}`}
          className="whitespace-nowrap"
        >
          {matchTitleShort(next, playoffType)}
          <ChevronRightIcon className="inline size-4 align-[-0.2em]" />
        </Link>
      )}
    </nav>
  );
}
