import { type Database, onValue, ref } from 'firebase/database';
import { useEffect, useMemo, useState } from 'react';

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

interface UseFirebaseWebcastsResult {
  webcasts: Record<string, WebcastWithMeta>;
  isLoading: boolean;
}

/**
 * Hook that subscribes to Firebase Realtime Database for live webcasts.
 * Listens to both `live_events` and `special_webcasts` paths and merges them
 * into a single webcasts map.
 */
export function useFirebaseWebcasts(): UseFirebaseWebcastsResult {
  const [liveEvents, setLiveEvents] = useState<FirebaseLiveEvent[] | null>(
    null,
  );
  const [specialWebcasts, setSpecialWebcasts] = useState<
    FirebaseSpecialWebcast[] | null
  >(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Don't run on server
    if (typeof window === 'undefined') return;

    let liveEventsLoaded = false;
    let specialWebcastsLoaded = false;
    let unsubscribeLiveEvents: (() => void) | null = null;
    let unsubscribeSpecialWebcasts: (() => void) | null = null;

    const checkLoading = () => {
      if (liveEventsLoaded && specialWebcastsLoaded) {
        setIsLoading(false);
      }
    };

    // Initialize Firebase subscriptions
    void getDatabase().then((database) => {
      // Subscribe to live_events
      const liveEventsRef = ref(database, 'live_events');
      unsubscribeLiveEvents = onValue(liveEventsRef, (snapshot) => {
        const data = snapshot.val() as Record<string, FirebaseLiveEvent> | null;
        if (data) {
          const events: FirebaseLiveEvent[] = Object.values(data);
          setLiveEvents(events.filter((event) => event.webcasts?.length > 0));
        } else {
          setLiveEvents([]);
        }
        liveEventsLoaded = true;
        checkLoading();
      });

      // Subscribe to special_webcasts
      const specialWebcastsRef = ref(database, 'special_webcasts');
      unsubscribeSpecialWebcasts = onValue(specialWebcastsRef, (snapshot) => {
        const data = snapshot.val() as Record<
          string,
          FirebaseSpecialWebcast
        > | null;
        if (data) {
          setSpecialWebcasts(Object.values(data));
        } else {
          setSpecialWebcasts([]);
        }
        specialWebcastsLoaded = true;
        checkLoading();
      });
    });

    return () => {
      unsubscribeLiveEvents?.();
      unsubscribeSpecialWebcasts?.();
    };
  }, []);

  // Merge live events and special webcasts into a single map
  const webcasts = useMemo(() => {
    const result: Record<string, WebcastWithMeta> = {};

    // Process special webcasts first
    if (specialWebcasts) {
      specialWebcasts.forEach((webcast) => {
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
    if (liveEvents) {
      liveEvents.forEach((event) => {
        event.webcasts?.forEach((webcast, index) => {
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
  }, [liveEvents, specialWebcasts]);

  return {
    webcasts,
    isLoading,
  };
}
