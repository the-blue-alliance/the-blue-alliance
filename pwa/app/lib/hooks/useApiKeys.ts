import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  addApiReadKey,
  deleteApiReadKey,
  listApiKeys,
} from '~/api/tba/mobile/sdk.gen';
import type { ApiKeysResponse } from '~/api/tba/mobile/types.gen';
import { useAuth } from '~/components/tba/auth/auth';

export function useApiKeys() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const queryKey = ['apiKeys', user?.uid];

  const query = useQuery({
    queryKey,
    queryFn: async () => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const response = await listApiKeys({ auth: token });
      if (response.data === undefined) {
        throw new Error('Failed to load API keys');
      }
      return response.data;
    },
    enabled: !!user,
  });

  // Rather than refetch after a write, update the cache directly with the
  // authoritative key the backend returns. This is instant (no round-trip) and
  // avoids stale reads from the local Datastore emulator, which simulates
  // eventual consistency for the non-ancestor query used to list keys.
  // (Production Datastore is strongly consistent, but this is cheaper anyway.)
  const addMutation = useMutation({
    mutationFn: async (description: string) => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const response = await addApiReadKey({
        auth: token,
        body: { description },
      });
      const readKey = response.data?.read_key;
      if (!readKey) {
        throw new Error('Failed to add key');
      }
      return readKey;
    },
    onSuccess: (readKey) => {
      queryClient.setQueryData<ApiKeysResponse>(queryKey, (old) => ({
        read_keys: [...(old?.read_keys ?? []), readKey],
        write_keys: old?.write_keys ?? [],
      }));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (keyId: string) => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const response = await deleteApiReadKey({
        auth: token,
        body: { key_id: keyId },
      });
      // client_api_method always returns HTTP 200; logical failures are in the
      // body `code` (e.g. 404 not found, 401 expired token), so check it here.
      if (response.data?.code !== 200) {
        throw new Error('Failed to delete key');
      }
      return keyId;
    },
    onSuccess: (keyId) => {
      queryClient.setQueryData<ApiKeysResponse>(queryKey, (old) => ({
        read_keys: (old?.read_keys ?? []).filter((k) => k.key !== keyId),
        write_keys: old?.write_keys ?? [],
      }));
    },
  });

  return {
    readKeys: query.data?.read_keys ?? [],
    writeKeys: query.data?.write_keys ?? [],
    isLoading: query.isLoading,
    addReadKey: addMutation.mutateAsync,
    isAdding: addMutation.isPending,
    deleteReadKey: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
  };
}
