import json
import unittest
from unittest.mock import patch

import pytest

from backend.common.consts.media_type import MediaType, TYPE_NAMES
from backend.common.futures import InstantFuture
from backend.common.helpers.webcast_helper import WebcastParser
from backend.common.suggestions.media_parser import MediaParser
from backend.common.urlfetch import URLFetchResult


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


class TestMediaUrlParser(unittest.TestCase):
    def test_youtube_parse_long(self) -> None:
        yt_long = MediaParser.partial_media_dict_from_url(
            "http://www.youtube.com/watch?v=I-IrVbsl_K8"
        ).get_result()
        self.assertIsNotNone(yt_long)
        self.assertEqual(yt_long["media_type_enum"], MediaType.YOUTUBE_VIDEO)
        self.assertEqual(yt_long["foreign_key"], "I-IrVbsl_K8")

    def test_youtube_parse_short(self) -> None:
        yt_short = MediaParser.partial_media_dict_from_url(
            "http://youtu.be/I-IrVbsl_K8"
        ).get_result()
        self.assertIsNotNone(yt_short)
        self.assertEqual(yt_short["media_type_enum"], MediaType.YOUTUBE_VIDEO)
        self.assertEqual(yt_short["foreign_key"], "I-IrVbsl_K8")

    def test_youtube_parse_playlist(self) -> None:
        yt_from_playlist = MediaParser.partial_media_dict_from_url(
            "https://www.youtube.com/watch?v=VP992UKFbko&index=1&list=PLZT9pIgNOV6ZE0EgstWeoRWGWT3uoaszm"
        ).get_result()
        self.assertIsNotNone(yt_from_playlist)
        self.assertEqual(yt_from_playlist["media_type_enum"], MediaType.YOUTUBE_VIDEO)
        self.assertEqual(yt_from_playlist["foreign_key"], "VP992UKFbko")

    def test_youtube_parse_shorts(self) -> None:
        yt_shorts = MediaParser.partial_media_dict_from_url(
            "https://www.youtube.com/shorts/S8m53ArvTRc"
        ).get_result()
        self.assertIsNotNone(yt_shorts)
        self.assertEqual(yt_shorts["media_type_enum"], MediaType.YOUTUBE_VIDEO)
        self.assertEqual(yt_shorts["foreign_key"], "S8m53ArvTRc")

    @pytest.mark.skip(reason="CD media is dead")
    def test_cdphotothread_parsetest_cdphotothread_parse(self):
        cd = MediaParser.partial_media_dict_from_url(
            "https://www.chiefdelphi.com/media/photos/41999"
        )
        self.assertEqual(cd["media_type_enum"], MediaType.CD_PHOTO_THREAD)
        self.assertEqual(cd["foreign_key"], "41999")
        self.assertTrue(cd["details_json"])
        details = json.loads(cd["details_json"])
        self.assertEqual(
            details["image_partial"], "a88/a880fa0d65c6b49ddb93323bc7d2e901_l.jpg"
        )

    def test_imgur_parse(self) -> None:
        imgur_img = MediaParser.partial_media_dict_from_url(
            "http://imgur.com/zYqWbBh"
        ).get_result()
        self.assertIsNotNone(imgur_img)
        self.assertEqual(imgur_img["media_type_enum"], MediaType.IMGUR)
        self.assertEqual(imgur_img["foreign_key"], "zYqWbBh")

        imgur_img = MediaParser.partial_media_dict_from_url(
            "http://i.imgur.com/zYqWbBh.png"
        ).get_result()
        self.assertIsNotNone(imgur_img)
        self.assertEqual(imgur_img["media_type_enum"], MediaType.IMGUR)
        self.assertEqual(imgur_img["foreign_key"], "zYqWbBh")

        self.assertEqual(
            MediaParser.partial_media_dict_from_url(
                "http://imgur.com/r/aww"
            ).get_result(),
            None,
        )
        self.assertEqual(
            MediaParser.partial_media_dict_from_url(
                "http://imgur.com/a/album"
            ).get_result(),
            None,
        )

    def test_fb_profile_parse(self) -> None:
        result = MediaParser.partial_media_dict_from_url(
            "http://facebook.com/theuberbots"
        ).get_result()
        self.assertIsNotNone(result)
        self.assertEqual(result["media_type_enum"], MediaType.FACEBOOK_PROFILE)
        self.assertEqual(result["is_social"], True)
        self.assertEqual(result["foreign_key"], "theuberbots")
        self.assertEqual(result["site_name"], TYPE_NAMES[MediaType.FACEBOOK_PROFILE])
        self.assertEqual(result["profile_url"], "https://www.facebook.com/theuberbots")

    def test_twitter_profile_parse(self) -> None:
        result = MediaParser.partial_media_dict_from_url(
            "https://twitter.com/team1124"
        ).get_result()
        self.assertIsNotNone(result)
        self.assertEqual(result["media_type_enum"], MediaType.TWITTER_PROFILE)
        self.assertEqual(result["is_social"], True)
        self.assertEqual(result["foreign_key"], "team1124")
        self.assertEqual(result["site_name"], TYPE_NAMES[MediaType.TWITTER_PROFILE])
        self.assertEqual(result["profile_url"], "https://twitter.com/team1124")

    def test_youtube_profile_parse(self) -> None:
        result = MediaParser.partial_media_dict_from_url(
            "https://www.youtube.com/Uberbots1124"
        ).get_result()
        self.assertIsNotNone(result)
        self.assertEqual(result["media_type_enum"], MediaType.YOUTUBE_CHANNEL)
        self.assertEqual(result["is_social"], True)
        self.assertEqual(result["foreign_key"], "uberbots1124")
        self.assertEqual(result["site_name"], TYPE_NAMES[MediaType.YOUTUBE_CHANNEL])
        self.assertEqual(result["profile_url"], "https://www.youtube.com/uberbots1124")

        short_result = MediaParser.partial_media_dict_from_url(
            "https://www.youtube.com/Uberbots1124"
        ).get_result()
        self.assertIsNotNone(short_result)
        self.assertEqual(short_result["media_type_enum"], MediaType.YOUTUBE_CHANNEL)
        self.assertEqual(short_result["is_social"], True)
        self.assertEqual(short_result["foreign_key"], "uberbots1124")
        self.assertEqual(
            short_result["site_name"], TYPE_NAMES[MediaType.YOUTUBE_CHANNEL]
        )
        self.assertEqual(
            short_result["profile_url"], "https://www.youtube.com/uberbots1124"
        )

        gapps_result = MediaParser.partial_media_dict_from_url(
            "https://www.youtube.com/c/tnt3102org"
        ).get_result()
        self.assertIsNotNone(gapps_result)
        self.assertEqual(gapps_result["media_type_enum"], MediaType.YOUTUBE_CHANNEL)
        self.assertEqual(gapps_result["is_social"], True)
        self.assertEqual(gapps_result["foreign_key"], "tnt3102org")
        self.assertEqual(
            gapps_result["site_name"], TYPE_NAMES[MediaType.YOUTUBE_CHANNEL]
        )
        self.assertEqual(
            gapps_result["profile_url"], "https://www.youtube.com/tnt3102org"
        )

    def test_github_profile_parse(self) -> None:
        result = MediaParser.partial_media_dict_from_url(
            "https://github.com/frc1124"
        ).get_result()
        self.assertIsNotNone(result)
        self.assertEqual(result["media_type_enum"], MediaType.GITHUB_PROFILE)
        self.assertEqual(result["is_social"], True)
        self.assertEqual(result["foreign_key"], "frc1124")
        self.assertEqual(result["site_name"], TYPE_NAMES[MediaType.GITHUB_PROFILE])
        self.assertEqual(result["profile_url"], "https://github.com/frc1124")

    def test_gitlab_profile_parse(self) -> None:
        result = MediaParser.partial_media_dict_from_url(
            "https://gitlab.com/frc1124"
        ).get_result()
        self.assertIsNotNone(result)
        self.assertEqual(result["media_type_enum"], MediaType.GITLAB_PROFILE)
        self.assertEqual(result["is_social"], True)
        self.assertEqual(result["foreign_key"], "frc1124")
        self.assertEqual(result["site_name"], TYPE_NAMES[MediaType.GITLAB_PROFILE])
        self.assertEqual(result["profile_url"], "https://www.gitlab.com/frc1124")

    @pytest.mark.skip(
        reason="TODO: need to migrate off legacy IG oembed https://developers.facebook.com/docs/instagram/oembed"
    )
    def test_instagram_profile_parse(self) -> None:
        result = MediaParser.partial_media_dict_from_url(
            "https://www.instagram.com/4hteamneutrino"
        ).get_result()
        self.assertIsNotNone(result)
        self.assertEqual(result["media_type_enum"], MediaType.INSTAGRAM_PROFILE)
        self.assertEqual(result["is_social"], True)
        self.assertEqual(result["foreign_key"], "4hteamneutrino")
        self.assertEqual(result["site_name"], TYPE_NAMES[MediaType.INSTAGRAM_PROFILE])
        self.assertEqual(
            result["profile_url"], "https://www.instagram.com/4hteamneutrino"
        )

    def test_periscope_profile_parse(self) -> None:
        result = MediaParser.partial_media_dict_from_url(
            "https://www.periscope.tv/evolution2626"
        ).get_result()
        self.assertIsNotNone(result)
        self.assertEqual(result["media_type_enum"], MediaType.PERISCOPE_PROFILE)
        self.assertEqual(result["is_social"], True)
        self.assertEqual(result["foreign_key"], "evolution2626")
        self.assertEqual(result["site_name"], TYPE_NAMES[MediaType.PERISCOPE_PROFILE])
        self.assertEqual(
            result["profile_url"], "https://www.periscope.tv/evolution2626"
        )

    @unittest.skip("Hitting grabcad rate limits")
    def test_grabcad_link(self) -> None:
        result = MediaParser.partial_media_dict_from_url(
            "https://grabcad.com/library/2016-148-robowranglers-1"
        ).get_result()
        self.assertIsNotNone(result)
        self.assertEqual(result["media_type_enum"], MediaType.GRABCAD)
        self.assertEqual(result["is_social"], False)
        self.assertEqual(result["foreign_key"], "2016-148-robowranglers-1")
        details = json.loads(result["details_json"])
        self.assertEqual(details["model_name"], "2016 | 148 - Robowranglers")
        self.assertEqual(details["model_description"], "Renegade")
        self.assertEqual(
            details["model_image"],
            "https://d2t1xqejof9utc.cloudfront.net/screenshots/pics/bf832651cc688c27a78c224fbd07d9d7/card.jpg",
        )
        self.assertEqual(details["model_created"], "2016-09-19T11:52:23Z")

    @pytest.mark.skip
    def test_instagram_image(self) -> None:
        result = MediaParser.partial_media_dict_from_url(
            "https://www.instagram.com/p/BUnZiriBYre/"
        ).get_result()
        self.assertIsNotNone(result)
        self.assertEqual(result["media_type_enum"], MediaType.INSTAGRAM_IMAGE)
        self.assertEqual(result["foreign_key"], "BUnZiriBYre")
        details = json.loads(result["details_json"])
        self.assertEqual(details["title"], "FRC 195 @ 2017 Battlecry @ WPI")
        self.assertEqual(details["author_name"], "1stroboticsrocks")
        self.assertIsNotNone(details.get("thumbnail_url", None))

    def test_unsupported_url_parse(self) -> None:
        self.assertEqual(
            MediaParser.partial_media_dict_from_url("http://foo.bar").get_result(), None
        )

    def test_cd_thread_parse_success(self) -> None:
        urls = [
            "https://www.chiefdelphi.com/t/team-254-presents-2025-undertow-technical-binder-code-q-a/506115",
            "https://www.chiefdelphi.com/t/team-254-presents-2025-undertow-technical-binder-code-q-a/506115?u=stray_username",
            "https://www.chiefdelphi.com/t/team-254-presents-2025-undertow-technical-binder-code-q-a/506115?u=1234",
            "https://www.chiefdelphi.com/t/506115",
            "https://www.chiefdelphi.com/t/team-254-presents-2025-undertow-technical-binder-code-q-a/506115/10",
            "https://www.chiefdelphi.com/t/team-254-presents-2025-undertow-technical-binder-code-q-a/506115/10?u=stray_username",
            "https://www.chiefdelphi.com/t/team-254-presents-2025-undertow-technical-binder-code-q-a/506115/10?u=1234",
        ]

        mock_content = json.dumps(
            {
                "title": "Team 254 presents 2025 Undertow technical binder code Q&A",
                "image_url": "https://www.chiefdelphi.com/uploads/default/optimized/4X/8/6/8/8681c45bd475d3f1b23f3af4f7b3a77df8a0e1cf_2_1024x750.jpeg",
            }
        )

        for url in urls:
            with self.subTest(url=url):
                mock_urlfetch_result = URLFetchResult.mock_urlfetch_result(
                    "https://www.chiefdelphi.com/t/506115.json", 200, mock_content
                )
                mock_future = InstantFuture(mock_urlfetch_result)

                with patch(
                    "google.appengine.ext.ndb.Context.urlfetch",
                    return_value=mock_future,
                ):
                    result = MediaParser.partial_media_dict_from_url(url).get_result()
                    self.assertIsNotNone(result)
                    self.assertEqual(result["media_type_enum"], MediaType.CD_THREAD)
                    self.assertEqual(result["foreign_key"], "506115")
                    self.assertEqual(
                        result["site_name"], TYPE_NAMES[MediaType.CD_THREAD]
                    )
                    self.assertEqual(
                        result["profile_url"], "https://www.chiefdelphi.com/t/506115"
                    )
                    self.assertEqual(
                        result["details_json"],
                        json.dumps(
                            {
                                "thread_title": "Team 254 presents 2025 Undertow technical binder code Q&A",
                                "image_url": "https://www.chiefdelphi.com/uploads/default/optimized/4X/8/6/8/8681c45bd475d3f1b23f3af4f7b3a77df8a0e1cf_2_1024x750.jpeg",
                            }
                        ),
                    )

    def test_cd_thread_parse_cd_unavailable(self) -> None:
        mock_urlfetch_result = URLFetchResult.mock_urlfetch_result(
            "https://www.chiefdelphi.com/t/506115.json", 500, ""
        )
        mock_future = InstantFuture(mock_urlfetch_result)

        with patch(
            "google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future
        ):
            result = MediaParser.partial_media_dict_from_url(
                "https://www.chiefdelphi.com/t/team-254-presents-2025-undertow-technical-binder-code-q-a/506115/10"
            ).get_result()
            self.assertIsNone(result)


class TestOnshapeParser(unittest.TestCase):
    ONSHAPE_URL = "https://cad.onshape.com/documents/5481081f48161555332968ff/w/a466cec29af372ec09c44333/e/abc123"

    def test_onshape_api_non_200(self) -> None:
        mock_urlfetch_result = URLFetchResult.mock_urlfetch_result(
            "https://cad.onshape.com/api/documents/d/5481081f48161555332968ff", 404, ""
        )
        mock_future = InstantFuture(mock_urlfetch_result)

        with patch(
            "google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future
        ):
            result = MediaParser.partial_media_dict_from_url(
                self.ONSHAPE_URL
            ).get_result()
            self.assertIsNone(result)

    def test_onshape_api_empty_response(self) -> None:
        mock_urlfetch_result = URLFetchResult.mock_urlfetch_result(
            "https://cad.onshape.com/api/documents/d/5481081f48161555332968ff",
            404,
            "",
        )
        mock_future = InstantFuture(mock_urlfetch_result)

        with patch(
            "google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future
        ):
            result = MediaParser.partial_media_dict_from_url(
                self.ONSHAPE_URL
            ).get_result()
            self.assertIsNone(result)

    def test_onshape_api_missing_fields(self) -> None:
        mock_urlfetch_result = URLFetchResult.mock_urlfetch_result(
            "https://cad.onshape.com/api/documents/d/5481081f48161555332968ff",
            200,
            json.dumps({"id": "abc"}),
        )
        mock_future = InstantFuture(mock_urlfetch_result)

        with patch(
            "google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future
        ):
            result = MediaParser.partial_media_dict_from_url(
                self.ONSHAPE_URL
            ).get_result()
            self.assertIsNotNone(result)
            details = json.loads(result["details_json"])
            self.assertEqual(details["model_name"], "")
            self.assertEqual(details["model_description"], "")
            self.assertEqual(details["model_created"], "")

    def test_onshape_api_success(self) -> None:
        mock_content = json.dumps(
            {
                "name": "Test Model",
                "description": "A test CAD model",
                "createdAt": "2024-01-01T00:00:00Z",
            }
        )
        mock_urlfetch_result = URLFetchResult.mock_urlfetch_result(
            "https://cad.onshape.com/api/documents/d/5481081f48161555332968ff",
            200,
            mock_content,
        )
        mock_future = InstantFuture(mock_urlfetch_result)

        with patch(
            "google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future
        ):
            result = MediaParser.partial_media_dict_from_url(
                self.ONSHAPE_URL
            ).get_result()
            self.assertIsNotNone(result)
            self.assertEqual(result["media_type_enum"], MediaType.ONSHAPE)
            details = json.loads(result["details_json"])
            self.assertEqual(details["model_name"], "Test Model")
            self.assertEqual(details["model_description"], "A test CAD model")
            self.assertEqual(details["model_created"], "2024-01-01T00:00:00Z")
            self.assertIn("model_image", details)


class TestWebcastUrlParser(unittest.TestCase):
    def testTwitchUrl(self) -> None:
        res = WebcastParser.webcast_dict_from_url("http://twitch.tv/frcgamesense")
        self.assertIsNotNone(res)
        self.assertEqual(res["type"], "twitch")
        self.assertEqual(res["channel"], "frcgamesense")

        unknown = WebcastParser.webcast_dict_from_url("http://twitch.tv/")
        self.assertIsNone(unknown)

    def testYouTubeUrl(self) -> None:
        yt_long = WebcastParser.webcast_dict_from_url(
            "http://www.youtube.com/watch?v=I-IrVbsl_K8"
        )
        self.assertIsNotNone(yt_long)
        self.assertEqual(yt_long["type"], "youtube")
        self.assertEqual(yt_long["channel"], "I-IrVbsl_K8")

        yt_short = WebcastParser.webcast_dict_from_url("http://youtu.be/I-IrVbsl_K8")
        self.assertIsNotNone(yt_short)
        self.assertEqual(yt_short["type"], "youtube")
        self.assertEqual(yt_short["channel"], "I-IrVbsl_K8")

        bad_long = WebcastParser.webcast_dict_from_url('"http://www.youtube.com/')
        self.assertIsNone(bad_long)

        bad_short = WebcastParser.webcast_dict_from_url("http://youtu.be/")
        self.assertIsNone(bad_short)

    @pytest.mark.skip(reason="we don't have ustream suggestions anymore")
    def testUstream(self):
        res = WebcastParser.webcast_dict_from_url("http://www.ustream.tv/decoraheagles")
        self.assertIsNotNone(res)
        self.assertEqual(res["type"], "ustream")
        self.assertEqual(res["channel"], "3064708")

        bad = WebcastParser.webcast_dict_from_url("http://ustream.tv/")
        self.assertIsNone(bad)

    def testUnknownUrl(self) -> None:
        bad = WebcastParser.webcast_dict_from_url("http://mywebsite.somewebcast")
        self.assertIsNone(bad)
