import json
import unittest2

from google.appengine.ext import testbed

from consts.media_type import MediaType
from helpers.media_helper import MediaParser
from helpers.webcast_helper import WebcastParser


class TestMediaUrlParser(unittest2.TestCase):
    def setUp(cls):
        cls.testbed = testbed.Testbed()
        cls.testbed.activate()
        cls.testbed.init_urlfetch_stub()

    def tearDown(cls):
        cls.testbed.deactivate()

    def test_youtube_parse(self):
        yt_long = MediaParser.partial_media_dict_from_url("http://www.youtube.com/watch?v=I-IrVbsl_K8")
        self.assertEqual(yt_long['media_type_enum'], MediaType.YOUTUBE_VIDEO)
        self.assertEqual(yt_long['foreign_key'], "I-IrVbsl_K8")

        yt_short = MediaParser.partial_media_dict_from_url("http://youtu.be/I-IrVbsl_K8")
        self.assertEqual(yt_short['media_type_enum'], MediaType.YOUTUBE_VIDEO)
        self.assertEqual(yt_short['foreign_key'], "I-IrVbsl_K8")

        yt_from_playlist = MediaParser.partial_media_dict_from_url("https://www.youtube.com/watch?v=VP992UKFbko&index=1&list=PLZT9pIgNOV6ZE0EgstWeoRWGWT3uoaszm")
        self.assertEqual(yt_from_playlist['media_type_enum'], MediaType.YOUTUBE_VIDEO)
        self.assertEqual(yt_from_playlist['foreign_key'], 'VP992UKFbko')

    # def test_cdphotothread_parsetest_cdphotothread_parse(self):
    #     cd = MediaParser.partial_media_dict_from_url(
    #         "https://www.chiefdelphi.com/media/photos/41999")
    #     self.assertEqual(cd['media_type_enum'], MediaType.CD_PHOTO_THREAD)
    #     self.assertEqual(cd['foreign_key'], "41999")
    #     self.assertTrue(cd['details_json'])
    #     details = json.loads(cd['details_json'])
    #     self.assertEqual(details['image_partial'], "a88/a880fa0d65c6b49ddb93323bc7d2e901_l.jpg")

    def test_imgur_parse(self):
        imgur_img = MediaParser.partial_media_dict_from_url("http://imgur.com/zYqWbBh")
        self.assertEqual(imgur_img['media_type_enum'], MediaType.IMGUR)
        self.assertEqual(imgur_img['foreign_key'], "zYqWbBh")

        imgur_img = MediaParser.partial_media_dict_from_url("http://i.imgur.com/zYqWbBh.png")
        self.assertEqual(imgur_img['media_type_enum'], MediaType.IMGUR)
        self.assertEqual(imgur_img['foreign_key'], "zYqWbBh")

        self.assertEqual(MediaParser.partial_media_dict_from_url("http://imgur.com/r/aww"), None)
        self.assertEqual(MediaParser.partial_media_dict_from_url("http://imgur.com/a/album"), None)

    def test_fb_profile_parse(self):
        result = MediaParser.partial_media_dict_from_url("http://facebook.com/theuberbots")
        self.assertEqual(result['media_type_enum'], MediaType.FACEBOOK_PROFILE)
        self.assertEqual(result['is_social'], True)
        self.assertEqual(result['foreign_key'], 'theuberbots')
        self.assertEqual(result['site_name'], MediaType.type_names[MediaType.FACEBOOK_PROFILE])
        self.assertEqual(result['profile_url'], 'https://www.facebook.com/theuberbots')

    def test_twitter_profile_parse(self):
        result = MediaParser.partial_media_dict_from_url("https://twitter.com/team1124")
        self.assertEqual(result['media_type_enum'], MediaType.TWITTER_PROFILE)
        self.assertEqual(result['is_social'], True)
        self.assertEqual(result['foreign_key'], 'team1124')
        self.assertEqual(result['site_name'], MediaType.type_names[MediaType.TWITTER_PROFILE])
        self.assertEqual(result['profile_url'], 'https://twitter.com/team1124')

    def test_youtube_profile_parse(self):
        result = MediaParser.partial_media_dict_from_url("https://www.youtube.com/Uberbots1124")
        self.assertEqual(result['media_type_enum'], MediaType.YOUTUBE_CHANNEL)
        self.assertEqual(result['is_social'], True)
        self.assertEqual(result['foreign_key'], 'uberbots1124')
        self.assertEqual(result['site_name'], MediaType.type_names[MediaType.YOUTUBE_CHANNEL])
        self.assertEqual(result['profile_url'], 'https://www.youtube.com/uberbots1124')

        short_result = MediaParser.partial_media_dict_from_url("https://www.youtube.com/Uberbots1124")
        self.assertEqual(short_result['media_type_enum'], MediaType.YOUTUBE_CHANNEL)
        self.assertEqual(short_result['is_social'], True)
        self.assertEqual(short_result['foreign_key'], 'uberbots1124')
        self.assertEqual(short_result['site_name'], MediaType.type_names[MediaType.YOUTUBE_CHANNEL])
        self.assertEqual(short_result['profile_url'], 'https://www.youtube.com/uberbots1124')

        gapps_result = MediaParser.partial_media_dict_from_url("https://www.youtube.com/c/tnt3102org")
        self.assertEqual(gapps_result['media_type_enum'], MediaType.YOUTUBE_CHANNEL)
        self.assertEqual(gapps_result['is_social'], True)
        self.assertEqual(gapps_result['foreign_key'], 'tnt3102org')
        self.assertEqual(gapps_result['site_name'], MediaType.type_names[MediaType.YOUTUBE_CHANNEL])
        self.assertEqual(gapps_result['profile_url'], 'https://www.youtube.com/tnt3102org')

    def test_github_profile_parse(self):
        result = MediaParser.partial_media_dict_from_url("https://github.com/frc1124")
        self.assertEqual(result['media_type_enum'], MediaType.GITHUB_PROFILE)
        self.assertEqual(result['is_social'], True)
        self.assertEqual(result['foreign_key'], 'frc1124')
        self.assertEqual(result['site_name'], MediaType.type_names[MediaType.GITHUB_PROFILE])
        self.assertEqual(result['profile_url'], 'https://github.com/frc1124')

    def test_instagram_profile_parse(self):
        result = MediaParser.partial_media_dict_from_url("https://www.instagram.com/4hteamneutrino")
        self.assertEqual(result['media_type_enum'], MediaType.INSTAGRAM_PROFILE)
        self.assertEqual(result['is_social'], True)
        self.assertEqual(result['foreign_key'], '4hteamneutrino')
        self.assertEqual(result['site_name'], MediaType.type_names[MediaType.INSTAGRAM_PROFILE])
        self.assertEqual(result['profile_url'], 'https://www.instagram.com/4hteamneutrino')

    def test_periscope_profile_parse(self):
        result = MediaParser.partial_media_dict_from_url("https://www.periscope.tv/evolution2626")
        self.assertEqual(result['media_type_enum'], MediaType.PERISCOPE_PROFILE)
        self.assertEqual(result['is_social'], True)
        self.assertEqual(result['foreign_key'], 'evolution2626')
        self.assertEqual(result['site_name'], MediaType.type_names[MediaType.PERISCOPE_PROFILE])
        self.assertEqual(result['profile_url'], 'https://www.periscope.tv/evolution2626')

    def test_grabcad_link(self):
        result = MediaParser.partial_media_dict_from_url("https://grabcad.com/library/2016-148-robowranglers-1")
        self.assertEqual(result['media_type_enum'], MediaType.GRABCAD)
        self.assertEqual(result['is_social'], False)
        self.assertEqual(result['foreign_key'], '2016-148-robowranglers-1')
        details = json.loads(result['details_json'])
        self.assertEqual(details['model_name'], '2016 | 148 - Robowranglers')
        self.assertEqual(details['model_description'], 'Renegade')
        self.assertEqual(details['model_image'], 'https://d2t1xqejof9utc.cloudfront.net/screenshots/pics/96268d5c5e6c1b7fe8892f713813bb40/card.jpg')
        self.assertEqual(details['model_created'], '2016-09-19T11:52:23Z')

    def test_instagram_image(self):
        result = MediaParser.partial_media_dict_from_url("https://www.instagram.com/p/BUnZiriBYre/")
        self.assertEqual(result['media_type_enum'], MediaType.INSTAGRAM_IMAGE)
        self.assertEqual(result['foreign_key'], "BUnZiriBYre")
        details = json.loads(result['details_json'])
        self.assertEqual(details['title'], "FRC 195 @ 2017 Battlecry @ WPI")
        self.assertEqual(details['author_name'], '1stroboticsrocks')
        self.assertIsNotNone(details.get('thumbnail_url', None))

    def test_unsupported_url_parse(self):
        self.assertEqual(MediaParser.partial_media_dict_from_url("http://foo.bar"), None)


class TestWebcastUrlParser(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testbed = testbed.Testbed()
        cls.testbed.activate()
        cls.testbed.init_urlfetch_stub()

    @classmethod
    def tearDownClass(cls):
        cls.testbed.deactivate()

    def testTwitchUrl(self):
        res = WebcastParser.webcast_dict_from_url("http://twitch.tv/frcgamesense")
        self.assertIsNotNone(res)
        self.assertEqual(res['type'], 'twitch')
        self.assertEqual(res['channel'], 'frcgamesense')

        unknown = WebcastParser.webcast_dict_from_url("http://twitch.tv/")
        self.assertIsNone(unknown)

    def testYouTubeUrl(self):
        yt_long = WebcastParser.webcast_dict_from_url("http://www.youtube.com/watch?v=I-IrVbsl_K8")
        self.assertIsNotNone(yt_long)
        self.assertEqual(yt_long['type'], 'youtube')
        self.assertEqual(yt_long['channel'], 'I-IrVbsl_K8')

        yt_short = WebcastParser.webcast_dict_from_url("http://youtu.be/I-IrVbsl_K8")
        self.assertIsNotNone(yt_short)
        self.assertEqual(yt_short['type'], 'youtube')
        self.assertEqual(yt_short['channel'], 'I-IrVbsl_K8')

        bad_long = WebcastParser.webcast_dict_from_url('"http://www.youtube.com/')
        self.assertIsNone(bad_long)

        bad_short = WebcastParser.webcast_dict_from_url("http://youtu.be/")
        self.assertIsNone(bad_short)

    def testUstream(self):
        res = WebcastParser.webcast_dict_from_url('http://www.ustream.tv/decoraheagles')
        self.assertIsNotNone(res)
        self.assertEqual(res['type'], 'ustream')
        self.assertEqual(res['channel'], '3064708')

        bad = WebcastParser.webcast_dict_from_url('http://ustream.tv/')
        self.assertIsNone(bad)

    def testUnknownUrl(self):
        bad = WebcastParser.webcast_dict_from_url("http://mywebsite.somewebcast")
        self.assertIsNone(bad)
