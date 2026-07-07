import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  acceptModerationSuggestion,
  getModerationQueue,
  listModerationSuggestions,
  rejectModerationSuggestions,
} from '~/api/tba/moderation/sdk.gen';
import type {
  AcceptRequest,
  AcceptResponse,
  SuggestionType,
} from '~/api/tba/moderation/types.gen';
import { useAuth } from '~/components/tba/auth/auth';

export interface ReviewDecisions {
  accepts: { key: string; overrides: AcceptRequest }[];
  rejects: string[];
}

export interface ReviewSubmissionResult {
  accepted: string[];
  rejected: string[];
  /** Another moderator got there first; the suggestion is no longer pending. */
  alreadyReviewed: string[];
  failed: { key: string; message: string }[];
}

export function useModerationQueue() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ['moderation', 'queue', user?.uid],
    queryFn: async () => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const response = await getModerationQueue({
        auth: token,
        throwOnError: true,
      });
      return response.data;
    },
    enabled: !!user,
    retry: false,
  });
}

export function useModerationSuggestions(suggestionType: SuggestionType) {
  const { user } = useAuth();
  return useQuery({
    queryKey: ['moderation', 'suggestions', suggestionType, user?.uid],
    queryFn: async () => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const response = await listModerationSuggestions({
        auth: token,
        path: { suggestion_type: suggestionType },
        throwOnError: true,
      });
      return response.data;
    },
    enabled: !!user,
    retry: false,
  });
}

export function useReviewSubmission(suggestionType: SuggestionType) {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      accepts,
      rejects,
    }: ReviewDecisions): Promise<ReviewSubmissionResult> => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const result: ReviewSubmissionResult = {
        accepted: [],
        rejected: [],
        alreadyReviewed: [],
        failed: [],
      };

      // Accepts are processed one at a time, matching the backend's
      // per-suggestion transactions
      for (const accept of accepts) {
        const response = await acceptModerationSuggestion({
          auth: token,
          path: { suggestion_key: accept.key },
          body: accept.overrides,
        });
        const outcome = (response.data ?? response.error) as
          AcceptResponse | undefined;
        if (outcome?.result === 'accepted') {
          result.accepted.push(accept.key);
        } else if (outcome?.result === 'already_reviewed') {
          result.alreadyReviewed.push(accept.key);
        } else {
          result.failed.push({
            key: accept.key,
            message: outcome?.message ?? outcome?.result ?? 'request failed',
          });
        }
      }

      if (rejects.length > 0) {
        const response = await rejectModerationSuggestions({
          auth: token,
          body: { suggestion_keys: rejects },
        });
        for (const outcome of response.data?.results ?? []) {
          if (outcome.result === 'rejected') {
            result.rejected.push(outcome.suggestion_key);
          } else if (outcome.result === 'already_reviewed') {
            result.alreadyReviewed.push(outcome.suggestion_key);
          } else {
            result.failed.push({
              key: outcome.suggestion_key,
              message: outcome.message ?? outcome.result,
            });
          }
        }
      }

      return result;
    },
    onSettled: () => {
      void queryClient.invalidateQueries({
        queryKey: ['moderation', 'suggestions', suggestionType],
      });
      void queryClient.invalidateQueries({
        queryKey: ['moderation', 'queue'],
      });
    },
  });
}
