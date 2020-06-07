import json

from backend.common.models.sitevar import Sitevar


class WebsiteBlacklist:
    @staticmethod
    def _default_sitevar() -> Sitevar:
        return Sitevar.get_or_insert(
            "website_blacklist", values_json=json.dumps({"websites": []})
        )

    @staticmethod
    def is_blacklisted(website: str) -> bool:
        website_blacklist_sitevar = WebsiteBlacklist._default_sitevar()
        website_blacklist = website_blacklist_sitevar.contents.get("websites", [])
        return website in website_blacklist

    @staticmethod
    def blacklist(website: str):
        website_blacklist_sitevar = WebsiteBlacklist._default_sitevar()
        website_blacklist = website_blacklist_sitevar.contents.get("websites", [])
        if website in website_blacklist:
            return
        website_blacklist.append(website)
        website_blacklist_sitevar.contents = {"websites": website_blacklist}
        website_blacklist_sitevar.put()
