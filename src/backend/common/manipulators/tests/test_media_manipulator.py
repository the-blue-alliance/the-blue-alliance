import unittest

import pytest
from google.cloud import ndb

from backend.common.consts.media_type import MediaType
from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.models.media import Media
from backend.common.models.team import Team


@pytest.mark.usefixtures("ndb_context")
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
