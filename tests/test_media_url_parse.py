import json

import unittest2

from google.appengine.ext import testbed

from consts.media_type import MediaType
from helpers.media_helper import MediaParser


class TestMediaUrlParser(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.testbed = testbed.Testbed()
        cls.testbed.activate()
        cls.testbed.init_urlfetch_stub()

    @classmethod
    def tearDownClass(cls):
        cls.testbed.deactivate()

    def test_youtube_parse(self):
        yt_long = MediaParser.partial_media_dict_from_url("http://www.youtube.com/watch?v=I-IrVbsl_K8")
        self.assertEqual(yt_long['media_type_enum'], MediaType.YOUTUBE_VIDEO)
        self.assertEqual(yt_long['foreign_key'], "I-IrVbsl_K8")

        yt_short = MediaParser.partial_media_dict_from_url("http://youtu.be/I-IrVbsl_K8")
        self.assertEqual(yt_short['media_type_enum'], MediaType.YOUTUBE_VIDEO)
        self.assertEqual(yt_short['foreign_key'], "I-IrVbsl_K8")

    def test_cdphotothread_parse(self):
        cd = MediaParser.partial_media_dict_from_url("http://www.chiefdelphi.com/media/photos/41999")
        self.assertEqual(cd['media_type_enum'], MediaType.CD_PHOTO_THREAD)
        self.assertEqual(cd['foreign_key'], "41999")
        self.assertTrue(cd['details_json'])
        details = json.loads(cd['details_json'])
        self.assertEqual(details['image_partial'], "a88/a880fa0d65c6b49ddb93323bc7d2e901_l.jpg")

    def test_imgur_parse(self):
        imgur_img = MediaParser.partial_media_dict_from_url("http://imgur.com/zYqWbBh")
        self.assertEqual(imgur_img['media_type_enum'], MediaType.IMGUR)
        self.assertEqual(imgur_img['foreign_key'], "zYqWbBh")

        imgur_img = MediaParser.partial_media_dict_from_url("http://i.imgur.com/zYqWbBh.png")
        self.assertEqual(imgur_img['media_type_enum'], MediaType.IMGUR)
        self.assertEqual(imgur_img['foreign_key'], "zYqWbBh")

        self.assertEqual(MediaParser.partial_media_dict_from_url("http://imgur.com/r/aww"), None)
        self.assertEqual(MediaParser.partial_media_dict_from_url("http://imgur.com/a/album"), None)

    def test_unsupported_url_parse(self):
        self.assertEqual(MediaParser.partial_media_dict_from_url("http://foo.bar"), None)