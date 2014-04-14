import unittest2

from google.appengine.ext import testbed

from consts.media_type import MediaType
from helpers.media_helper import MediaParser

class TestMediaUrlParser(unittest2.TestCase):

    def test_youtube_parse(self):
        yt_long = MediaParser.partial_media_dict_from_url("http://www.youtube.com/watch?v=I-IrVbsl_K8")
        self.assertEqual(yt_long['media_type_enum'],MediaType.YOUTUBE)
        self.assertEqual(yt_long['foreign_key'],"I-IrVbsl_K8")

        yt_short = MediaParser.partial_media_dict_from_url("http://youtu.be/I-IrVbsl_K8")
        self.assertEqual(yt_short['media_type_enum'],MediaType.YOUTUBE)
        self.assertEqual(yt_short['foreign_key'],"I-IrVbsl_K8")

    def test_imgur_parse(self):        
        imgur_img = MediaParser.partial_media_dict_from_url("http://imgur.com/zYqWbBh")
        self.assertEqual(imgur_img['media_type_enum'],MediaType.IMGUR)
        self.assertEqual(imgur_img['foreign_key'],"zYqWbBh")

        self.assertEqual(MediaParser.partial_media_dict_from_url("http://imgur.com/r/aww"),None)
        self.assertEqual(MediaParser.partial_media_dict_from_url("http://imgur.com/a/album"),None)

    def test_unsupported_url_parse(self):
        self.assertEqual(MediaParser.partial_media_dict_from_url("http://foo.bar"),None)

