import { useQuery, useQueryClient } from '@tanstack/react-query';
import { type Database, onValue, ref } from 'firebase/database';
import { useEffect, useMemo } from 'react';

import {
  type FirebaseLiveEvent,
  type FirebaseSpecialWebcast,
  type WebcastWithMeta,
  getWebcastId,
} from '~/lib/gameday/types';

// Lazy load database to avoid SSR issues
let cachedDatabase: Database | null = null;
async function getDatabase(): Promise<Database> {
  if (cachedDatabase) return cachedDatabase;
  const { database } = await import('~/firebase/firebaseConfig');
  cachedDatabase = database;
  return database;
}

export const FIREBASE_LIVE_EVENTS_QUERY_KEY = [
  'firebase',
  'live_events',
] as const;
export const FIREBASE_SPECIAL_WEBCASTS_QUERY_KEY = [
  'firebase',
  'special_webcasts',
] as const;

interface UseFirebaseWebcastsResult {
  webcasts: Record<string, WebcastWithMeta>;
  isLoading: boolean;
}

/**
 * Hook that subscribes to Firebase Realtime Database for live webcasts.
 * Listens to both `live_events` and `special_webcasts` paths and merges them
 * into a single webcasts map.
 *
 * Firebase data is piped into TanStack Query's cache via setQueryData so it
 * is visible in the ReactQueryDevtools panel.
 */
export function useFirebaseWebcasts(): UseFirebaseWebcastsResult {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Don't run on server
    if (typeof window === 'undefined') return;

    let unsubscribeLiveEvents: (() => void) | null = null;
    let unsubscribeSpecialWebcasts: (() => void) | null = null;

    // Initialize Firebase subscriptions
    void getDatabase().then((database) => {
      // Subscribe to live_events
      const liveEventsRef = ref(database, 'live_events');
      unsubscribeLiveEvents = onValue(liveEventsRef, (snapshot) => {
        queryClient.setQueryData(
          FIREBASE_LIVE_EVENTS_QUERY_KEY,
          snapshot.val() as Record<string, FirebaseLiveEvent> | null,
        );
      });

      // Subscribe to special_webcasts
      const specialWebcastsRef = ref(database, 'special_webcasts');
      unsubscribeSpecialWebcasts = onValue(specialWebcastsRef, (snapshot) => {
        queryClient.setQueryData(
          FIREBASE_SPECIAL_WEBCASTS_QUERY_KEY,
          snapshot.val() as Record<string, FirebaseSpecialWebcast> | null,
        );
      });
    });

    return () => {
      unsubscribeLiveEvents?.();
      unsubscribeSpecialWebcasts?.();
    };
  }, [queryClient]);

  // Read from TQ cache — data is populated by the effect above via setQueryData.
  // enabled: false means TQ never fetches on its own; isPending is true until
  // setQueryData is called for the first time (i.e. Firebase hasn't responded yet).
  const { data: liveEventsData, isPending: liveEventsPending } =
    useQuery<Record<string, FirebaseLiveEvent> | null>({
      queryKey: [...FIREBASE_LIVE_EVENTS_QUERY_KEY],
      enabled: false,
      staleTime: Infinity,
    });

  const { data: specialWebcastsData, isPending: specialWebcastsPending } =
    useQuery<Record<string, FirebaseSpecialWebcast> | null>({
      queryKey: [...FIREBASE_SPECIAL_WEBCASTS_QUERY_KEY],
      enabled: false,
      staleTime: Infinity,
    });

  // Merge live events and special webcasts into a single map
  const webcasts = useMemo(() => {
    const result: Record<string, WebcastWithMeta> = {};

    // Process special webcasts first
    if (specialWebcastsData) {
      Object.values(specialWebcastsData).forEach((webcast) => {
        const id = getWebcastId(webcast.key_name, 0);
        result[id] = {
          id,
          name: webcast.name,
          webcast: {
            type: webcast.type,
            channel: webcast.channel,
            file: webcast.file,
            status: webcast.status,
            stream_title: webcast.stream_title,
            viewer_count: webcast.viewer_count,
          },
          isSpecial: true,
        };
      });
    }

    // Process live events
    if (liveEventsData) {
      Object.values(liveEventsData)
        .filter((event) => event.webcasts?.length > 0)
        .forEach((event) => {
          event.webcasts.forEach((webcast, index) => {
            let name = event.short_name || event.name;
            if (event.webcasts.length > 1) {
              name = `${name} ${index + 1}`;
            }

            const id = getWebcastId(event.key, index);
            result[id] = {
              id,
              name,
              webcast: {
                type: webcast.type,
                channel: webcast.channel,
                file: webcast.file,
                status: webcast.status,
                stream_title: webcast.stream_title,
                viewer_count: webcast.viewer_count,
              },
              isSpecial: false,
            };
          });
        });
    }

    return result;
  }, [liveEventsData, specialWebcastsData]);

  return {
    webcasts,
    isLoading: liveEventsPending || specialWebcastsPending,
  };
}
