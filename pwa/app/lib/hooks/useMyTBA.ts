import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';

import {
  listFavorites,
  listSubscriptions,
  setModelPreferences,
} from '~/api/tba/mobile/sdk.gen';
import type {
  FavoriteCollection,
  ModelType,
  NotificationType,
  SubscriptionCollection,
} from '~/api/tba/mobile/types.gen';
import { useAuth } from '~/components/tba/auth/auth';

interface UseMyTBAResult {
  isFavorite: boolean;
  notifications: NotificationType[];
  toggleFavorite: () => void;
  setPreferences: (
    favorite: boolean,
    notifications: NotificationType[],
  ) => void;
  isPending: boolean;
}

export function useMyTBA(
  modelKey: string,
  modelType: ModelType,
): UseMyTBAResult {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const favoritesQueryKey = ['favorites', user?.uid];
  const subscriptionsQueryKey = ['subscriptions', user?.uid];

  const { data: favorites } = useQuery({
    queryKey: favoritesQueryKey,
    queryFn: async () => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const response = await listFavorites({ auth: token });
      return response.data;
    },
    enabled: !!user,
  });

  const { data: subscriptions } = useQuery({
    queryKey: subscriptionsQueryKey,
    queryFn: async () => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const response = await listSubscriptions({ auth: token });
      return response.data;
    },
    enabled: !!user,
  });

  const isFavorite = useMemo(
    () => favorites?.favorites?.some((f) => f.model_key === modelKey) ?? false,
    [favorites, modelKey],
  );

  const notifications = useMemo(() => {
    const sub = subscriptions?.subscriptions?.find(
      (s) => s.model_key === modelKey,
    );
    return sub?.notifications ?? [];
  }, [subscriptions, modelKey]);

  const mutation = useMutation({
    mutationFn: async ({
      favorite,
      notifs,
    }: {
      favorite: boolean;
      notifs: NotificationType[];
    }) => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      return setModelPreferences({
        auth: token,
        body: {
          model_key: modelKey,
          model_type: modelType,
          device_key: null,
          notifications: notifs,
          favorite,
        },
      });
    },
    onMutate: async ({ favorite, notifs }) => {
      await queryClient.cancelQueries({ queryKey: favoritesQueryKey });
      await queryClient.cancelQueries({ queryKey: subscriptionsQueryKey });

      const prevFavorites =
        queryClient.getQueryData<FavoriteCollection>(favoritesQueryKey);
      const prevSubscriptions =
        queryClient.getQueryData<SubscriptionCollection>(subscriptionsQueryKey);

      queryClient.setQueryData<FavoriteCollection>(favoritesQueryKey, (old) => {
        const existing = old?.favorites ?? [];
        const filtered = existing.filter((f) => f.model_key !== modelKey);
        return {
          favorites: favorite
            ? [...filtered, { model_key: modelKey, model_type: modelType }]
            : filtered,
        };
      });

      queryClient.setQueryData<SubscriptionCollection>(
        subscriptionsQueryKey,
        (old) => {
          const existing = old?.subscriptions ?? [];
          const filtered = existing.filter((s) => s.model_key !== modelKey);
          return {
            subscriptions:
              notifs.length > 0
                ? [
                    ...filtered,
                    {
                      model_key: modelKey,
                      model_type: modelType,
                      notifications: notifs,
                    },
                  ]
                : filtered,
          };
        },
      );

      return { prevFavorites, prevSubscriptions };
    },
    onError: (_err, _vars, context) => {
      if (context?.prevFavorites) {
        queryClient.setQueryData(favoritesQueryKey, context.prevFavorites);
      }
      if (context?.prevSubscriptions) {
        queryClient.setQueryData(
          subscriptionsQueryKey,
          context.prevSubscriptions,
        );
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: favoritesQueryKey });
      void queryClient.invalidateQueries({ queryKey: subscriptionsQueryKey });
    },
  });

  const toggleFavorite = useCallback(() => {
    mutation.mutate({ favorite: !isFavorite, notifs: notifications });
  }, [mutation, isFavorite, notifications]);

  const setPreferences = useCallback(
    (favorite: boolean, notifs: NotificationType[]) => {
      mutation.mutate({ favorite, notifs });
    },
    [mutation],
  );

  return {
    isFavorite,
    notifications,
    toggleFavorite,
    setPreferences,
    isPending: mutation.isPending,
  };
}
