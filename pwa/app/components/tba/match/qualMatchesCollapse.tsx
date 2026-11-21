import { useState } from 'react';

import ChevronDownIcon from '~icons/lucide/chevron-down';

import type { Match } from '~/api/tba/read';
import { Button } from '~/components/ui/button';
import { matchHasBeenPlayed } from '~/lib/matchUtils';

export default function QualMatchesCollapse({
  matches,
  hasElims,
  children,
}: {
  matches: Match[];
  hasElims: boolean;
  children: React.ReactNode;
}) {
  const [expanded, setExpanded] = useState(false);

  if (!hasElims || !matches.every(matchHasBeenPlayed)) {
    return children;
  }

  return (
    <>
      <Button
        variant="outline"
        className="mb-2 w-full gap-2 lg:hidden"
        aria-expanded={expanded}
        onClick={() => setExpanded(!expanded)}
      >
        {expanded
          ? 'Hide qualification matches'
          : `Show all ${matches.length} qualification matches`}
        <ChevronDownIcon className={`size-4 ${expanded ? 'rotate-180' : ''}`} />
      </Button>
      <div className={expanded ? undefined : 'max-lg:hidden'}>{children}</div>
    </>
  );
}
