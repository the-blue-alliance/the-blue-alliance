import unittest2

from helpers.website_helper import WebsiteHelper


class TestWebsiteHelper(unittest2.TestCase):
    def test_format_url(self):
        # No scheme
        self.assertEqual(WebsiteHelper.format_url('website.com'), 'http://website.com')
        self.assertEqual(WebsiteHelper.format_url(' website.com '), 'http://website.com')
        self.assertEqual(WebsiteHelper.format_url('website.com/path'), 'http://website.com/path')
        self.assertEqual(WebsiteHelper.format_url('website.com/path/subpath'), 'http://website.com/path/subpath')
        self.assertEqual(WebsiteHelper.format_url('subdomain.website.com'), 'http://subdomain.website.com')
        self.assertEqual(WebsiteHelper.format_url('subdomain.website.com/path'), 'http://subdomain.website.com/path')

        # Provided HTTP
        self.assertEqual(WebsiteHelper.format_url('http://website.com'), 'http://website.com')
        self.assertEqual(WebsiteHelper.format_url(' http://website.com '), 'http://website.com')
        self.assertEqual(WebsiteHelper.format_url('http://website.com/path'), 'http://website.com/path')
        self.assertEqual(WebsiteHelper.format_url('http://website.com/path/subpath'), 'http://website.com/path/subpath')
        self.assertEqual(WebsiteHelper.format_url('http://subdomain.website.com'), 'http://subdomain.website.com')
        self.assertEqual(WebsiteHelper.format_url('http://subdomain.website.com/path'), 'http://subdomain.website.com/path')

        # Provided HTTPS
        self.assertEqual(WebsiteHelper.format_url('https://website.com'), 'https://website.com')
        self.assertEqual(WebsiteHelper.format_url(' https://website.com '), 'https://website.com')
        self.assertEqual(WebsiteHelper.format_url('https://website.com/path'), 'https://website.com/path')
        self.assertEqual(WebsiteHelper.format_url('https://website.com/path/subpath'), 'https://website.com/path/subpath')
        self.assertEqual(WebsiteHelper.format_url('https://subdomain.website.com'), 'https://subdomain.website.com')
        self.assertEqual(WebsiteHelper.format_url('https://subdomain.website.com/path'), 'https://subdomain.website.com/path')

        # Invalid URLs
        self.assertEqual(WebsiteHelper.format_url(u'websit\xe9.com'), None)
        self.assertEqual(WebsiteHelper.format_url(u'http://websit\xe9.com'), None)
        self.assertEqual(WebsiteHelper.format_url(u'https://websit\xe9.com'), None)
        self.assertEqual(WebsiteHelper.format_url('ftp://website.com'), None)

        # Null URLs
        self.assertEqual(WebsiteHelper.format_url(None), None)
        self.assertEqual(WebsiteHelper.format_url(''), None)
