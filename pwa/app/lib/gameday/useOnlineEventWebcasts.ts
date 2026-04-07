import { useCallback, useMemo } from 'react';

import type { Event } from '~/api/tba/read';
import { isEventActive } from '~/lib/eventUtils';
import { useFirebaseWebcasts } from '~/lib/gameday/useFirebaseWebcasts';

/**
 * Returns a function that checks whether a given event has a live stream.
 * Uses Firebase webcast status when loaded, falling back to date-based logic
 * while Firebase is still loading.
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
    (event: Event) =>
      isLoading ? isEventActive(event) : onlineEventKeys.has(event.key),
    [isLoading, onlineEventKeys],
  );
}
