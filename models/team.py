import logging

from google.appengine.ext import ndb

class Team(ndb.Model):
    """
    Teams represent FIRST Robotics Competition teams.
    key_name is like 'frc177'
    """
    team_number = ndb.IntegerProperty(required=True)
    name = ndb.StringProperty(indexed=False)
    nickname = ndb.StringProperty(indexed=False)
    address = ndb.StringProperty(indexed=False)
    website = ndb.StringProperty(indexed=False)
    first_tpid = ndb.IntegerProperty() #from USFIRST. FIRST team ID number. -greg 5/20/2010
    first_tpid_year = ndb.IntegerProperty() # from USFIRST. Year tpid is applicable for. -greg 9 Jan 2011
    
    def __init__(self, *args, **kw):
        self._country_name = None
        self._locality = None
        self._region = None
        super(Team, self).__init__(*args, **kw)

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
            address_parts = self.address.split(",")
            if len(address_parts) == 3:
                self._country_name = address_parts.pop().strip()
                self._region = address_parts.pop().strip()
                self._locality = address_parts.pop().strip()
            if len(address_parts) == 2:
                region_country = address_parts.pop().strip().split(" ")
                if len(region_country) == 2:
                    self._country_name = region_country.pop().strip()
                self._region = region_country.pop().strip()
                self._locality = address_parts.pop().strip()
        except Exception, e:
            logging.warning("Error on team.split_address: %s", e)
    
    @property 
    def details_url(self):
        return "/team/%s" % self.team_number

    @property
    def key_name(self):
        return "frc%s" % self.team_number
