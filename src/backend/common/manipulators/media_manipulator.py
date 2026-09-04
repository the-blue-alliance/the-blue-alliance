import logging
from typing import List, Set

from backend.common.cache_clearing import get_affected_queries
from backend.common.consts.media_type import MediaType
from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.media import Media


class MediaManipulator(ManipulatorBase[Media]):
    """
    Handle Media database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.media_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls,
        new_model: Media,
        old_model: Media,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> Media:
        old_reference_kinds = {r.kind() for r in old_model.references}
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        cls._enforce_smugmug_reference_kinds(old_model, old_reference_kinds)
        return old_model

    @classmethod
    def _enforce_smugmug_reference_kinds(
        cls, media: Media, old_reference_kinds: Set[str]
    ) -> None:
        """
        A SmugMug photo belongs to a team, and a SmugMug album belongs to either a
        team or an event but never both. References are auto-unioned on merge, so
        drop anything the incoming write would have added in violation of that.
        """
        if media.media_type_enum == MediaType.SMUGMUG_PHOTO:
            allowed_kinds = {"Team"}
        elif media.media_type_enum == MediaType.SMUGMUG_ALBUM:
            allowed_kinds = old_reference_kinds or {
                r.kind() for r in media.references[:1]
            }
        else:
            return

        allowed = [r for r in media.references if r.kind() in allowed_kinds]
        if len(allowed) == len(media.references):
            return

        logging.warning(
            "Dropping references {} from {} - only {} references are allowed".format(
                [r.id() for r in media.references if r.kind() not in allowed_kinds],
                media.key_name,
                sorted(allowed_kinds),
            )
        )
        media.references = allowed
        media.preferred_references = [
            r for r in media.preferred_references if r.kind() in allowed_kinds
        ]
