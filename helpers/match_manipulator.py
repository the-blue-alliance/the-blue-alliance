import json

from google.appengine.ext import ndb

from cache_clearer.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase
from models.team import Team


class MatchManipulator(ManipulatorBase):
    """
    Handle Match database writes.
    """
    @classmethod
    def clearCache(self, match):
        CacheClearer.clear_match_and_references(
            [match.key],
            [match.event],
            set([ndb.Key(Team, team_key_name) for team_key_name in match.team_key_names]),
            [match.event.id()[:4]]
        )

    @classmethod
    def updateMerge(self, new_match, old_match, auto_union=True):
        """
        Given an "old" and a "new" Match object, replace the fields in the
        "old" team that are present in the "new" team, but keep fields from
        the "old" team that are null in the "new" team.
        """
        # build set of referenced keys for cache clearing
        match_keys = set()
        event_keys = set()
        team_keys = set()
        years = set()
        for m in [old_match, new_match]:
            match_keys.add(m.key)
            event_keys.add(m.event)
            team_keys = team_keys.union(set([ndb.Key(Team, team_key_name) for team_key_name in m.team_key_names]))
            years.add(m.event.id()[:4])  # because the match model doesn't store the year

        immutable_attrs = [
            "comp_level",
            "event",
            "set_number",
            "match_number",
        ]  # These build key_name, and cannot be changed without deleting the model.

        attrs = [
            "game",
            "no_auto_update",
            "time",
            "time_string",
        ]

        json_attrs = [
            "alliances_json",
        ]

        list_attrs = [
            "team_key_names"
        ]

        auto_union_attrs = [
            "tba_videos",
            "youtube_videos"
        ]

        # if not auto_union, treat auto_union_attrs as list_attrs
        if not auto_union:
            list_attrs += auto_union_attrs
            auto_union_attrs = []

        for attr in attrs:
            if getattr(new_match, attr) is not None:
                if getattr(new_match, attr) != getattr(old_match, attr):
                    setattr(old_match, attr, getattr(new_match, attr))
                    old_match.dirty = True

        for attr in json_attrs:
            if getattr(new_match, attr) is not None:
                if json.loads(getattr(new_match, attr)) != json.loads(getattr(old_match, attr)):
                    setattr(old_match, attr, getattr(new_match, attr))
                    # changinging 'attr_json' doesn't clear lazy-loaded '_attr'
                    setattr(old_match, '_{}'.format(attr.replace('_json', '')), None)
                    old_match.dirty = True

        for attr in list_attrs:
            if len(getattr(new_match, attr)) > 0:
                if getattr(new_match, attr) != getattr(old_match, attr):
                    setattr(old_match, attr, getattr(new_match, attr))
                    old_match.dirty = True

        for attr in auto_union_attrs:
            old_set = set(getattr(old_match, attr))
            new_set = set(getattr(new_match, attr))
            unioned = old_set.union(new_set)
            if unioned != old_set:
                setattr(old_match, attr, list(unioned))
                old_match.dirty = True

        if getattr(old_match, 'dirty', False):
            CacheClearer.clear_match_and_references(match_keys, event_keys, team_keys, years)

        return old_match
