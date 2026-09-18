import { useQuery, useQueryClient } from '@tanstack/react-query';
import { onValue, ref } from 'firebase/database';
import { useEffect, useState } from 'react';

import type { MatchSuggestions } from '~/api/firebase';
import { getDatabaseInstance } from '~/firebase/firebaseConfig';

export const FIREBASE_MATCH_SUGGESTIONS_QUERY_KEY = [
  'firebase',
  'match_suggestions',
] as const;

export interface UseFirebaseMatchSuggestionsResult {
  data: MatchSuggestions | null | undefined;
  error: Error | null;
  isLoading: boolean;
}

export function useFirebaseMatchSuggestions(): UseFirebaseMatchSuggestionsResult {
  const queryClient = useQueryClient();
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    let active = true;
    let unsubscribe: (() => void) | null = null;

    void getDatabaseInstance()
      .then((database) => {
        if (!active) return;
        unsubscribe = onValue(
          ref(database, 'match_suggestions'),
          (snapshot) => {
            setError(null);
            queryClient.setQueryData(
              FIREBASE_MATCH_SUGGESTIONS_QUERY_KEY,
              snapshot.val() as MatchSuggestions | null,
            );
          },
          (firebaseError) => setError(firebaseError),
        );
      })
      .catch((databaseError: unknown) => {
        if (!active) return;
        setError(
          databaseError instanceof Error
            ? databaseError
            : new Error('Unable to connect to Firebase'),
        );
      });

    return () => {
      active = false;
      unsubscribe?.();
    };
  }, [queryClient]);

  const { data, isPending } = useQuery<MatchSuggestions | null>({
    queryKey: [...FIREBASE_MATCH_SUGGESTIONS_QUERY_KEY],
    queryFn: () => null,
    enabled: false,
    staleTime: Infinity,
  });

  return { data, error, isLoading: isPending && error === null };
}
