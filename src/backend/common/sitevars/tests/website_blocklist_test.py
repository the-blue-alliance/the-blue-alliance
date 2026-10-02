from backend.common.sitevars.website_blocklist import WebsiteBlocklist


def test_key():
    assert WebsiteBlocklist.key() == "website_blacklist"


def test_description():
    assert (
        WebsiteBlocklist.description()
        == "For blacklisting sketchy websites from team pages"
    )


def test_default_sitevar():
    default_sitevar = WebsiteBlocklist._fetch_sitevar()
    assert default_sitevar is not None
    assert default_sitevar.contents == {"websites": []}


def test_blacklist():
    website = "https://www.thebluealliance.com/"
    assert not WebsiteBlocklist.is_blacklisted(website)
    WebsiteBlocklist.blacklist(website)
    assert WebsiteBlocklist.is_blacklisted(website)


def test_blacklist_duplicate():
    website = "https://www.thebluealliance.com/"
    WebsiteBlocklist.blacklist(website)
    default_sitevar = WebsiteBlocklist._fetch_sitevar()
    assert default_sitevar.contents["websites"] == [website]
    WebsiteBlocklist.blacklist(website)
    default_sitevar = WebsiteBlocklist._fetch_sitevar()
    assert default_sitevar.contents["websites"] == [website]
