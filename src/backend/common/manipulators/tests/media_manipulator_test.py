import unittest

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.media_type import MediaType
from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.models.event import Event
from backend.common.models.media import Media
from backend.common.models.team import Team


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestMediaManipulator(unittest.TestCase):
    def setUp(self):
        self.old_media = Media(
            id="youtube_asdf",
            media_type_enum=MediaType.YOUTUBE_VIDEO,
            foreign_key="asdf",
            year=2012,
            references=[ndb.Key(Team, "frc177")],
        )

        self.new_media = Media(
            id="youtube_asdf",
            media_type_enum=MediaType.YOUTUBE_VIDEO,
            foreign_key="asdf",
            year=2012,
            references=[ndb.Key(Team, "frc176")],
        )

    def assertMergedMedia(self, media: Media) -> None:
        self.assertOldMedia(media)
        self.assertTrue(ndb.Key(Team, "frc176") in media.references)

    def assertOldMedia(self, media: Media) -> None:
        self.assertEqual(media.media_type_enum, MediaType.YOUTUBE_VIDEO)
        self.assertEqual(media.foreign_key, "asdf"),
        self.assertEqual(media.year, 2012)
        self.assertTrue(ndb.Key(Team, "frc177") in media.references)

    def test_createOrUpdate(self):
        MediaManipulator.createOrUpdate(self.old_media)
        self.assertOldMedia(Media.get_by_id("youtube_asdf"))
        MediaManipulator.createOrUpdate(self.new_media)
        self.assertMergedMedia(Media.get_by_id("youtube_asdf"))

    def test_findOrSpawn(self):
        self.old_media.put()
        self.assertMergedMedia(MediaManipulator.findOrSpawn(self.new_media))

    def test_updateMerge(self):
        self.assertMergedMedia(
            MediaManipulator.updateMerge(self.new_media, self.old_media)
        )


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestSmugmugReferenceKinds(unittest.TestCase):
    def _media(self, media_type: MediaType, references) -> Media:
        return Media(
            id=Media.render_key_name(media_type, "asdf"),
            media_type_enum=media_type,
            foreign_key="asdf",
            year=2026,
            references=references,
        )

    def test_album_on_team_rejects_an_event(self) -> None:
        media_id = Media.render_key_name(MediaType.SMUGMUG_ALBUM, "asdf")
        MediaManipulator.createOrUpdate(
            self._media(MediaType.SMUGMUG_ALBUM, [ndb.Key(Team, "frc177")])
        )
        MediaManipulator.createOrUpdate(
            self._media(MediaType.SMUGMUG_ALBUM, [ndb.Key(Event, "2026necmp")])
        )
        assert none_throws(Media.get_by_id(media_id)).references == [
            ndb.Key(Team, "frc177")
        ]

    def test_album_on_event_rejects_a_team(self) -> None:
        media_id = Media.render_key_name(MediaType.SMUGMUG_ALBUM, "asdf")
        MediaManipulator.createOrUpdate(
            self._media(MediaType.SMUGMUG_ALBUM, [ndb.Key(Event, "2026necmp")])
        )
        MediaManipulator.createOrUpdate(
            self._media(MediaType.SMUGMUG_ALBUM, [ndb.Key(Team, "frc177")])
        )
        assert none_throws(Media.get_by_id(media_id)).references == [
            ndb.Key(Event, "2026necmp")
        ]

    def test_album_accepts_more_of_the_same_kind(self) -> None:
        media_id = Media.render_key_name(MediaType.SMUGMUG_ALBUM, "asdf")
        MediaManipulator.createOrUpdate(
            self._media(MediaType.SMUGMUG_ALBUM, [ndb.Key(Team, "frc177")])
        )
        MediaManipulator.createOrUpdate(
            self._media(MediaType.SMUGMUG_ALBUM, [ndb.Key(Team, "frc176")])
        )
        assert set(none_throws(Media.get_by_id(media_id)).references) == {
            ndb.Key(Team, "frc177"),
            ndb.Key(Team, "frc176"),
        }

    def test_photo_rejects_an_event(self) -> None:
        media_id = Media.render_key_name(MediaType.SMUGMUG_PHOTO, "asdf")
        MediaManipulator.createOrUpdate(
            self._media(MediaType.SMUGMUG_PHOTO, [ndb.Key(Team, "frc177")])
        )
        MediaManipulator.createOrUpdate(
            self._media(MediaType.SMUGMUG_PHOTO, [ndb.Key(Event, "2026necmp")])
        )
        assert none_throws(Media.get_by_id(media_id)).references == [
            ndb.Key(Team, "frc177")
        ]

    def test_other_media_types_are_untouched(self) -> None:
        MediaManipulator.createOrUpdate(
            self._media(MediaType.YOUTUBE_VIDEO, [ndb.Key(Team, "frc177")])
        )
        MediaManipulator.createOrUpdate(
            self._media(MediaType.YOUTUBE_VIDEO, [ndb.Key(Event, "2026necmp")])
        )
        assert set(none_throws(Media.get_by_id("youtube_asdf")).references) == {
            ndb.Key(Team, "frc177"),
            ndb.Key(Event, "2026necmp"),
        }
