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
        if not website_url.startswith('http://') and not website_url.startswith('https://') and not website_url.startswith('ftp://'):
            formatted_url = 'http://{}'.format(website_url)
        else:
            formatted_url = website_url

        return formatted_url
