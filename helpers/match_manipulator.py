import json
import logging

from google.appengine.ext import ndb

from helpers.cache_clearer import CacheClearer
from helpers.firebase.firebase_pusher import FirebasePusher
from helpers.manipulator_base import ManipulatorBase


class MatchManipulator(ManipulatorBase):
    """
    Handle Match database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_match_cache_keys_and_controllers(affected_refs)

    @classmethod
    def postUpdateHook(cls, matches):
        """
        To run after models have been updated
        """
        if matches:
            try:
                FirebasePusher.updated_event(matches[0].event.id())
            except Exception:
                logging.warning("Enqueuing Firebase push failed!")

    @classmethod
    def updateMerge(self, new_match, old_match, auto_union=True):
        """
        Given an "old" and a "new" Match object, replace the fields in the
        "old" team that are present in the "new" team, but keep fields from
        the "old" team that are null in the "new" team.
        """
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
            "score_breakdown_json",
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
                if (getattr(old_match, attr) is None) or (json.loads(getattr(new_match, attr)) != json.loads(getattr(old_match, attr))):
                    setattr(old_match, attr, getattr(new_match, attr))
                    # changinging 'attr_json' doesn't clear lazy-loaded '_attr'
                    setattr(old_match, '_{}'.format(attr.replace('_json', '')), None)
                    old_match.dirty = True

        for attr in list_attrs:
            if len(getattr(new_match, attr)) > 0:
                if set(getattr(new_match, attr)) != set(getattr(old_match, attr)):  # lists are treated as sets
                    setattr(old_match, attr, getattr(new_match, attr))
                    old_match.dirty = True

        for attr in auto_union_attrs:
            old_set = set(getattr(old_match, attr))
            new_set = set(getattr(new_match, attr))
            unioned = old_set.union(new_set)
            if unioned != old_set:
                setattr(old_match, attr, list(unioned))
                old_match.dirty = True

        return old_match
