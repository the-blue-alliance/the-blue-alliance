import { useQueries, useQuery } from '@tanstack/react-query';

import { listFavorites } from '~/api/tba/mobile/sdk.gen';
import type { TeamSimple } from '~/api/tba/read';
import { getTeamSimpleOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import { useAuth } from '~/components/tba/auth/auth';
import { MODEL_TYPE } from '~/lib/utils';

interface UseFavoriteTeamsResult {
  favoriteTeams: TeamSimple[];
  isLoading: boolean;
}

export function useFavoriteTeams(): UseFavoriteTeamsResult {
  const { user } = useAuth();

  const { data: favorites, isLoading: isFavoritesLoading } = useQuery({
    queryKey: ['favorites', user?.uid],
    queryFn: async () => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const response = await listFavorites({ auth: token });
      return response.data;
    },
    enabled: !!user,
  });

  const teamKeys = (favorites?.favorites ?? [])
    .filter((f) => f.model_type === MODEL_TYPE.TEAM)
    .map((f) => f.model_key);

  const favoriteTeams = useQueries({
    queries: teamKeys.map((key) =>
      getTeamSimpleOptions({ path: { team_key: key } }),
    ),
    combine: (results) => ({
      data: results
        .map((r) => r.data)
        .filter((t): t is TeamSimple => t !== undefined)
        .sort((a, b) => a.team_number - b.team_number),
      isLoading: results.some((r) => r.isLoading),
    }),
  });

  return {
    favoriteTeams: favoriteTeams.data,
    isLoading: isFavoritesLoading || favoriteTeams.isLoading,
  };
}
