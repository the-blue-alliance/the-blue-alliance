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
        self._country_name = None
        self._locality = None
        self._location = None
        self._region = None
        super(Team, self).__init__(*args, **kw)

    @property
    def championship_location(self):
        return ChampSplitHelper.get_champ(self)

    @property
    def country_name(self):
        if not self._country_name:
            self.split_address()
        return self._country_name

    @property
    def locality(self):
        if not self._locality:
            self.split_address()
        return self._locality

    @property
    def region(self):
        if not self._region:
            self.split_address()
        return self._region

    def split_address(self):
        """
        Return the various parts of a team address.
        Start like, 'South Windsor, CT USA'
        """
        try:
            if self.address is not None:
                address_parts = self.address.split(",")
                if len(address_parts) == 3:
                    self._country_name = address_parts.pop().strip()
                    self._region = address_parts.pop().strip()
                    self._locality = address_parts.pop().strip()
                elif len(address_parts) == 2:
                    region_country = address_parts.pop().strip().split(" ")
                    if len(region_country) == 2:
                        self._country_name = region_country.pop().strip()
                    self._region = region_country.pop().strip()
                    self._locality = address_parts.pop().strip()
                elif len(address_parts) > 3:
                    self._country_name = address_parts[-1].strip()
                    self._region = address_parts[-2].strip()
                    self._locality = ','.join(address_parts[:-2])
        except Exception, e:
            logging.warning("Error on team.split_address: %s", e)

    @property
    def location(self):
        if self._location is None:
            split_location = []
            if self.city:
                split_location.append(self.city)
            if self.state_prov:
                split_location.append(self.state_prov)
            if self.country:
                split_location.append(self.country)
            self._location = ', '.join(split_location)
        return self._location

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
