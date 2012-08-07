import logging

from google.appengine.ext import db

class Team(db.Model):
    """
    Teams represent FIRST Robotics Competition teams.
    key_name is like 'frc177'
    """
    team_number = db.IntegerProperty(required=True)
    name = db.StringProperty(indexed=False)
    nickname = db.StringProperty(indexed=False)
    address = db.PostalAddressProperty(indexed=False)
    website = db.LinkProperty(indexed=False)
    first_tpid = db.IntegerProperty() #from USFIRST. FIRST team ID number. -greg 5/20/2010
    first_tpid_year = db.IntegerProperty() # from USFIRST. Year tpid is applicable for. -greg 9 Jan 2011
    
    def do_split_address(self):
        """
        Return the various parts of a team address.
        Start like, 'South Windsor, CT USA'
        """
        try:
            address_dict = dict()
            address_parts = self.address.split(",")
            if len(address_parts) > 0:
                address_dict["locality"] = address_parts[0].strip()
            if len(address_parts) > 1:
                address_parts = address_parts[1].split(" ")
                if len(address_parts) > 1:
                    address_dict["country_name"] = address_parts.pop().strip()
                address_dict["region"] = " ".join(address_parts).strip()
            logging.info("%s !!!" % self.address)
            address_sections = address_dict.values()
            address_sections.reverse()
            address_dict["full_address"] = ", ".join(address_sections)
            self.split_address = address_dict
        except Exception, e:
            logging.warning("Error on team.do_split_address: %s", e)
     
    def details_url(self):
        return "/team/%s" % self.team_number