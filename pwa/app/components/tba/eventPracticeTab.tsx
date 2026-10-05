import { useMemo } from 'react';

import InfoIcon from '~icons/lucide/info';

import { Event, Match } from '~/api/tba/read';
import { END_OF_DAY_BREAKER } from '~/components/tba/match/breakers';
import SimpleMatchRowsWithBreaks from '~/components/tba/match/matchRows';
import { sortMatchComparator } from '~/lib/matchUtils';

export default function EventPracticeTab({
  event,
  matches,
}: {
  event: Event;
  matches: Match[];
}) {
  const sortedMatches = useMemo(
    () => [...matches].sort(sortMatchComparator),
    [matches],
  );

  return (
    <>
      <h2 className="mb-2 text-xl font-medium">Practice Matches</h2>
      <p
        role="note"
        className="mb-4 flex items-center gap-2 rounded-lg border
          border-blue-300 bg-blue-50 px-4 py-3 text-sm text-blue-900
          dark:border-blue-800 dark:bg-blue-950 dark:text-blue-100"
      >
        <InfoIcon className="size-4 shrink-0 text-blue-600 dark:text-blue-300" />
        Results are not published for practice matches.
      </p>
      <SimpleMatchRowsWithBreaks
        matches={sortedMatches}
        event={event}
        breakers={[END_OF_DAY_BREAKER]}
      />
    </>
  );
}
