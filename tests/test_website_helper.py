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

    def test_exists(self):
        # Exists (200)
        self.assertEqual(WebsiteHelper.exists('https://www.google.com'), True)
        self.assertEqual(WebsiteHelper.exists('https://imgur.com'), True)
        self.assertEqual(WebsiteHelper.exists('http://imgur.com'), True)
        self.assertEqual(WebsiteHelper.exists('https://github.com/the-blue-alliance'), True)

        # Exists (301/302)
        self.assertEqual(WebsiteHelper.exists('http://google.com'), True)  # 301 -> 302 -> 200
        self.assertEqual(WebsiteHelper.exists('http://www.google.com'), True)  # 302 -> 200
        self.assertEqual(WebsiteHelper.exists('https://google.com'), True)  # 301 -> 200
        self.assertEqual(WebsiteHelper.exists('http://www.imgur.com'), True)  # 301 -> 200
        self.assertEqual(WebsiteHelper.exists('https://www.imgur.com'), True)  # 301 -> 200
        self.assertEqual(WebsiteHelper.exists('http://github.com/the-blue-alliance'), True)  # 301 -> 200
        self.assertEqual(WebsiteHelper.exists('http://www.github.com/the-blue-alliance'), True)  # 301 -> 301 -> 200

        # Missing
        self.assertEqual(WebsiteHelper.exists('https://www.google.com/_404'), False)
        self.assertEqual(WebsiteHelper.exists('https://imgur.com/_404'), False)
        self.assertEqual(WebsiteHelper.exists('https://github.com/_404'), False)
