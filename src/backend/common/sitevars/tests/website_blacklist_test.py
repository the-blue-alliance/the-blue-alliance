from backend.common.sitevars.website_blacklist import WebsiteBlacklist


def test_default_sitevar():
    default_sitevar = WebsiteBlacklist._fetch_sitevar()
    assert default_sitevar is not None
    assert default_sitevar.contents == {"websites": []}


def test_blacklist():
    website = "https://www.thebluealliance.com/"
    assert not WebsiteBlacklist.is_blacklisted(website)
    WebsiteBlacklist.blacklist(website)
    assert WebsiteBlacklist.is_blacklisted(website)


def test_blacklist_duplicate():
    website = "https://www.thebluealliance.com/"
    WebsiteBlacklist.blacklist(website)
    default_sitevar = WebsiteBlacklist._fetch_sitevar()
    assert default_sitevar.contents["websites"] == [website]
    WebsiteBlacklist.blacklist(website)
    default_sitevar = WebsiteBlacklist._fetch_sitevar()
    assert default_sitevar.contents["websites"] == [website]
