"""
Cached per-team favorite counts, a global stand-in for personalized favorites.

The memcache namespace is deliberately shared with
`TeamHelper.getPopularTeamsEvents`, which computes the same counts the same way;
a future change can migrate that call site onto this helper.
"""

from typing import Any, cast, Dict, List, Set

from backend.common.memcache import MemcacheClient
from backend.common.models.favorite import Favorite
from backend.common.models.keys import TeamKey


class TeamFavoriteCountsHelper:
    CACHE_NAMESPACE: str = "team-favorite-counts"
    CACHE_TTL_S: int = 24 * 60 * 60

    @classmethod
    def get_counts(cls, team_keys: Set[TeamKey]) -> Dict[TeamKey, int]:
        """
        How many users have favorited each team, backed by memcache.
        """
        memcache = MemcacheClient.get()
        ordered = sorted(team_keys)
        # memcache takes str keys just fine, and TeamHelper writes str keys into
        # this same namespace, so we have to match it to share the entries
        cached = memcache.get_multi(
            cast(List[bytes], ordered),
            namespace=cls.CACHE_NAMESPACE,
        )
        counts: Dict[TeamKey, int] = {
            cast(TeamKey, team_key): count
            for team_key, count in cached.items()
            if count is not None
        }

        missing = [team_key for team_key in ordered if team_key not in counts]
        if not missing:
            return counts

        # Kick off every count before resolving any of them
        new_counts = {
            team_key: future.get_result()
            for team_key, future in [
                (team_key, Favorite.query(Favorite.model_key == team_key).count_async())
                for team_key in missing
            ]
        }
        memcache.set_multi(
            cast(Dict[bytes, Any], new_counts),
            cls.CACHE_TTL_S,
            namespace=cls.CACHE_NAMESPACE,
        )
        counts.update(new_counts)
        return counts
