import json

from models.sitevar import Sitevar


class WebsiteBlacklist:

    @staticmethod
    def is_blacklisted(website):
        website_blacklist_sitevar = Sitevar.get_or_insert('website_blacklist', values_json=json.dumps({'websites': []}))
        website_blacklist = website_blacklist_sitevar.contents.get('websites', [])
        return website in website_blacklist

    @staticmethod
    def blacklist(website):
        website_blacklist_sitevar = Sitevar.get_or_insert('website_blacklist', values_json=json.dumps({'websites': []}))
        website_blacklist = website_blacklist_sitevar.contents.get('websites', [])
        if website in website_blacklist:
            return
        website_blacklist.append(website)
        website_blacklist_sitevar.contents = {'websites': website_blacklist}
        website_blacklist_sitevar.put()
