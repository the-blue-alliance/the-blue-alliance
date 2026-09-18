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
  QueueResponse,
  SuggestionType,
} from '~/api/tba/moderation/types.gen';
import { ReviewResult } from '~/api/tba/moderation/types.gen';
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

/**
 * The pending queue for the signed-in moderator, or `null` when the account
 * has no review permissions. A 403 is the normal answer for most users (the
 * account page asks for everyone), so it is data rather than a query error
 * that would be reported.
 */
export function useModerationQueue() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ['moderation', 'queue', user?.uid],
    queryFn: async (): Promise<QueueResponse | null> => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const response = await getModerationQueue({ auth: token });
      if (response.data) {
        return response.data;
      }
      if (response.response?.status === 403) {
        return null;
      }
      throw response.error ?? new Error('Failed to load moderation queue');
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
        if (outcome?.result === ReviewResult.ACCEPTED) {
          result.accepted.push(accept.key);
        } else if (outcome?.result === ReviewResult.ALREADY_REVIEWED) {
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
          if (outcome.result === ReviewResult.REJECTED) {
            result.rejected.push(outcome.suggestion_key);
          } else if (outcome.result === ReviewResult.ALREADY_REVIEWED) {
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
