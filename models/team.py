import logging
import re

from google.appengine.ext import ndb
from helpers.champ_split_helper import ChampSplitHelper


class Team(ndb.Model):
    """
    Teams represent FIRST Robotics Competition teams.
    key_name is like 'frc177'
    """
    team_number = ndb.IntegerProperty(required=True)
    name = ndb.TextProperty(indexed=False)
    nickname = ndb.StringProperty(indexed=False)
    city = ndb.StringProperty()  # Equivalent to locality. From FRCAPI
    state_prov = ndb.StringProperty()  # Equivalent to region. From FRCAPI
    country = ndb.StringProperty()  # From FRCAPI
    postalcode = ndb.StringProperty()  # From ElasticSearch only. String because it can be like "95126-1215"
    website = ndb.StringProperty(indexed=False)
    first_tpid = ndb.IntegerProperty()  # from USFIRST. FIRST team ID number. -greg 5/20/2010
    first_tpid_year = ndb.IntegerProperty()  # from USFIRST. Year tpid is applicable for. -greg 9 Jan 2011
    rookie_year = ndb.IntegerProperty()
    motto = ndb.StringProperty(indexed=False)

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            'key': set(),
        }
        self._location = None
        super(Team, self).__init__(*args, **kw)

    @property
    def championship_location(self):
        return ChampSplitHelper.get_champ(self)

    @property
    def location(self):
        if self._location is None:
            split_location = []
            if self.city:
                split_location.append(self.city)
            if self.state_prov:
                if self.postalcode:
                    split_location.append(self.state_prov + ' ' + self.postalcode)
                else:
                    split_location.append(self.state_prov)
            if self.country:
                split_location.append(self.country)
            self._location = ', '.join(split_location)
        return self._location

    @property
    def split_name(self):
        """
        Guessing sponsors by splitting name by '/' or '&'
        """
        split_name = re.split('/|&', self.name)
        return [x.strip() for x in split_name]

    @property
    def details_url(self):
        return "/team/%s" % self.team_number

    @property
    def key_name(self):
        return "frc%s" % self.team_number

    @classmethod
    def validate_key_name(self, team_key):
        key_name_regex = re.compile(r'^frc[1-9]\d*$')
        match = re.match(key_name_regex, team_key)
        return True if match else False

    @property
    def motto_without_quotes(self):
        if (self.motto[0] == self.motto[-1]) and self.motto.startswith(("'", '"')):
            return self.motto[1:-1]
        return self.motto
