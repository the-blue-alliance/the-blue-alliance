import { useSuspenseQuery } from '@tanstack/react-query';
import { useRouter, useSearch } from '@tanstack/react-router';
import { MatchLink } from 'app/components/tba/links';
import { Suspense, useRef } from 'react';

import {
  getEventOptions,
  getMatchOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import MatchDetails from '~/components/tba/match/matchDetails';
import {
  Credenza,
  CredenzaBody,
  CredenzaContent,
  CredenzaHeader,
  CredenzaTitle,
} from '~/components/ui/credenza';
import { PlayoffType } from '~/lib/api/PlayoffType';
import { isValidMatchKey, matchTitleShort } from '~/lib/matchUtils';

export function MatchModal() {
  const { matchKey } = useSearch({ from: '__root__' });
  const router = useRouter();

  const isOpen = !!matchKey && isValidMatchKey(matchKey);

  // Keep track of last valid matchKey to show during close animation
  const lastMatchKeyRef = useRef<string | null>(null);
  if (isOpen && matchKey) {
    lastMatchKeyRef.current = matchKey;
  }

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      // Replace state to close the modal (removes matchKey from search params)
      void router.navigate({
        to: '.',
        search: (prev: { matchKey?: string }) => ({
          ...prev,
          matchKey: undefined,
        }),
        replace: true,
        resetScroll: false,
      });
    }
  };

  // Use current matchKey if open, otherwise use last valid one during close animation
  const displayMatchKey = isOpen ? matchKey : lastMatchKeyRef.current;

  return (
    <Credenza open={isOpen} onOpenChange={handleOpenChange}>
      <CredenzaContent className="max-w-5xl sm:max-w-5xl">
        {displayMatchKey && (
          <Suspense fallback={<MatchModalSpinner />}>
            <MatchModalContent matchKey={displayMatchKey} />
          </Suspense>
        )}
      </CredenzaContent>
    </Credenza>
  );
}

function MatchModalContent({ matchKey }: { matchKey: string }) {
  const eventKey = matchKey.split('_')[0];

  const matchQuery = useSuspenseQuery(
    getMatchOptions({ path: { match_key: matchKey } }),
  );

  const eventQuery = useSuspenseQuery(
    getEventOptions({ path: { event_key: eventKey } }),
  );

  if (!matchQuery.data || !eventQuery.data) {
    return (
      <>
        <CredenzaHeader>
          <CredenzaTitle>Match not found</CredenzaTitle>
        </CredenzaHeader>
        <CredenzaBody>
          <p>The requested match could not be found.</p>
        </CredenzaBody>
      </>
    );
  }

  const match = matchQuery.data;
  const event = eventQuery.data;

  return (
    <>
      <CredenzaHeader>
        <CredenzaTitle>
          <MatchLink matchOrKey={match} event={event} noModal>
            {matchTitleShort(match, event.playoff_type ?? PlayoffType.CUSTOM)}
            {' - '}
            {event.name} {event.year}
          </MatchLink>
        </CredenzaTitle>
      </CredenzaHeader>
      <CredenzaBody className="max-h-[80vh] overflow-y-auto">
        <MatchDetails match={match} event={event} />
      </CredenzaBody>
    </>
  );
}

function MatchModalSpinner() {
  return (
    <>
      <CredenzaHeader>
        <CredenzaTitle>
          <div className="h-6 w-100 animate-pulse rounded bg-muted" />
        </CredenzaTitle>
      </CredenzaHeader>
      <CredenzaBody className="flex min-h-32 items-center justify-center">
        <div
          className="size-8 animate-spin rounded-full border-4 border-muted
            border-t-primary"
        />
      </CredenzaBody>
    </>
  );
}
