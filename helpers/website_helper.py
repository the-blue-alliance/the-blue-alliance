from google.appengine.ext import ndb


class WebsiteHelper(object):
    @classmethod
    def format_url(cls, website_url):
        """
        Updates a URL to have the correct format. For example, it will change
        "website.com" to "http://website.com", while keeping
        "https://website.com" the same.
        """
        if not website_url:
            return None

        formatted_url = None

        website_url = website_url.strip()

        # Ensure all ASCII
        if not all(ord(c) < 128 for c in website_url):
            return None

        url_parts = website_url.split('://')
        if len(url_parts) == 1:
            formatted_url = 'http://{}'.format(website_url)
        elif url_parts[0] in {'http', 'https'}:
            formatted_url = website_url

        return formatted_url

    @classmethod
    def exists(cls, website_url):
        """
        Verify that a given URL exists (returns a non-404 status code)
        """
        context = ndb.get_context()

        if not website_url:
            return False

        result = context.urlfetch(website_url).get_result()

        return result.status_code != 404
