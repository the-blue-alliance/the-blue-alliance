"""
An extension of urlfetch that keeps cookies between redirects
From: http://everydayscripting.blogspot.com/2009/08/google-app-engine-cookie-handling-with.html
"""

import urllib
import urllib2
import Cookie
from google.appengine.api import urlfetch


class URLOpener:
    def __init__(self):
        self.cookie = Cookie.SimpleCookie()

    def open(self, url, data=None):
        if data is None:
            method = urlfetch.GET
        else:
            method = urlfetch.POST

        while url is not None:
            response = urlfetch.fetch(url=url,
                                      payload=data,
                                      method=method,
                                      headers=self._getHeaders(self.cookie),
                                      allow_truncated=False,
                                      follow_redirects=False,
                                      deadline=10
                                      )
            data = None  # Next request will be a get, so no need to send the data again.
            method = urlfetch.GET
            self.cookie.load(response.headers.get('set-cookie', ''))  # Load the cookies from the response
            url = response.headers.get('location')

        return response

    def _getHeaders(self, cookie):
        headers = {
            'Cookie': self._makeCookieHeader(cookie)
        }
        return headers

    def _makeCookieHeader(self, cookie):
        cookieHeader = ""
        for value in cookie.values():
            cookieHeader += "%s=%s; " % (value.key, value.value)
        return cookieHeader
