import re

from google.appengine.ext import ndb


class District(ndb.Model):
    """
    One instance of a district in a year. Here, we store info about a district and in-season data
    (like district rankings)
    """
    year = ndb.IntegerProperty()
    abbreviation = ndb.StringProperty()
    display_name = ndb.StringProperty()  # This is what we'll show on the TBA site
    elasticsearch_name = ndb.StringProperty()  # These names are in the event's name as returned by FRC Elasticsearch

    rankings = ndb.JsonProperty()  # District rankings as calculated by TBA
    advancement = ndb.JsonProperty()  # Dict of team key -> advancement data

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            'key': set(),
            'year': set(),
            'abbreviation': set(),
        }
        super(District, self).__init__(*args, **kw)

    @property
    def key_name(self):
        return "{}{}".format(self.year, self.abbreviation)

    @property
    def render_name(self):
        return self.display_name if self.display_name else "{}".format(self.abbreviation).upper()

    @classmethod
    def validate_key_name(self, district_key):
        key_name_regex = re.compile(r'^[1-9]\d{3}[a-z]+[0-9]?$')
        match = re.match(key_name_regex, district_key)
        return True if match else False

    @classmethod
    def renderKeyName(cls, year, district_abbrev):
        # Like 2016ne or 2016fim
        return "{}{}".format(year, district_abbrev.lower())
