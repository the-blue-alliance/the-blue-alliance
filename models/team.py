import logging
import re

from google.appengine.ext import ndb
from models.location import Location


class Team(ndb.Model):
    """
    Teams represent FIRST Robotics Competition teams.
    key_name is like 'frc177'
    """
    team_number = ndb.IntegerProperty(required=True)
    name = ndb.TextProperty(indexed=False)
    nickname = ndb.StringProperty(indexed=False)
    school_name = ndb.TextProperty(indexed=False)
    home_cmp = ndb.StringProperty()

    # city, state_prov, country, and postalcode are from FIRST
    city = ndb.StringProperty()  # Equivalent to locality. From FRCAPI
    state_prov = ndb.StringProperty()  # Equivalent to region. From FRCAPI
    country = ndb.StringProperty()  # From FRCAPI
    postalcode = ndb.StringProperty()  # From ElasticSearch only. String because it can be like "95126-1215"
    # Normalized address from the Google Maps API, constructed using the above
    normalized_location = ndb.StructuredProperty(Location)

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
        self._city_state_country = None
        super(Team, self).__init__(*args, **kw)

    @property
    def championship_location(self):
        from models.event import Event
        if self.home_cmp and self.updated:
            event = Event.get_by_id("{}{}".format(self.updated.year, self.home_cmp))
            if event and event.city:
                return {self.updated.year: event.city}
        return None

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
    def city_state_country(self):
        if not self._city_state_country and self.nl:
            self._city_state_country = self.nl.city_state_country

        if not self._city_state_country:
            location_parts = []
            if self.city:
                location_parts.append(self.city)
            if self.state_prov:
                location_parts.append(self.state_prov)
            if self.country:
                country = self.country
                if self.country == 'US':
                    country = 'USA'
                location_parts.append(country)
            self._city_state_country = ', '.join(location_parts)
        return self._city_state_country

    @property
    def nl(self):
        return None  # 2017-03-25 Normalized location too inconsistent. Completely disable for now. -fangeugene
        # if self.normalized_location and self.normalized_location.country not in {'United States', 'Canada'}:
        #     return False
        # return self.normalized_location

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
