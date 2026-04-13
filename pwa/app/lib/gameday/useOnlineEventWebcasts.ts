import { useCallback, useMemo } from 'react';

import type { Event } from '~/api/tba/read';
import { useFirebaseWebcasts } from '~/lib/gameday/useFirebaseWebcasts';

/**
 * Returns a function that checks whether a given event has a live stream.
 * Returns false while Firebase is still loading so buttons show as 'offline'
 * (but remain clickable) until real webcast status is available.
 */
export function useOnlineEventWebcasts(): (event: Event) => boolean {
  const { webcasts, isLoading } = useFirebaseWebcasts();

  const onlineEventKeys = useMemo(() => {
    const online = new Set<string>();
    Object.entries(webcasts).forEach(([id, { webcast, isSpecial }]) => {
      if (!isSpecial && webcast.status === 'online') {
        // id format is `${eventKey}-${index}`
        online.add(id.substring(0, id.lastIndexOf('-')));
      }
    });
    return online;
  }, [webcasts]);

  return useCallback(
    (event: Event) => !isLoading && onlineEventKeys.has(event.key),
    [isLoading, onlineEventKeys],
  );
}
