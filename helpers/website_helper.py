class WebsiteHelper(object):
    @classmethod
    def format_url(cls, website_url):
        """
        Updates a URL to have the correct format. For example, it will change
        "website.com" to "http://website.com", while keeping
        "https://website.com" the same.
        """
        formatted_url = None

        website_url = website_url.strip()
        if not website_url.startswith('http://') and not website_url.startswith('https://'):
            formatted_url = website_url
        else:
            formatted_url = 'http://{}'.format(website_url)

        return formatted_url
