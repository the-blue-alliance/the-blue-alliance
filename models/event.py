from google.appengine.ext import db

class Event(db.Model):
    """
    Events represent FIRST Robotics Competition events, both official and unofficial.
    key_name is like '2010ct'
    """
    name = db.StringProperty()
    event_type = db.StringProperty(indexed=False) # From USFIRST
    short_name = db.StringProperty(indexed=False) # Should not contain "Regional" or "Division", like "Hartford"
    event_short = db.StringProperty(required=True, indexed=False) # Smaller abbreviation like "CT"
    year = db.IntegerProperty(required=True)
    start_date = db.DateTimeProperty()
    end_date = db.DateTimeProperty()
    venue = db.StringProperty(indexed=False)
    venue_address = db.PostalAddressProperty(indexed=False) # We can scrape this.
    location = db.StringProperty(indexed=False)
    official = db.BooleanProperty(default=False) # Is the event FIRST-official?
    first_eid = db.StringProperty() #from USFIRST
    facebook_eid = db.StringProperty(indexed=False) #from Facebook
    website = db.StringProperty(indexed=False)
    webcast_url = db.StringProperty(indexed=False)
    oprs = db.ListProperty(float, indexed=False)
    opr_teams = db.ListProperty(int, indexed=False)
    
    def get_key_name(self):
        """
        Returns the string of the key_name of the Event object before writing it.
        """
        return str(self.year) + self.event_short
    
    def getFacebookEventUrl(self):
        """
        Return a string of the Facebook Event URL.
        """
        return "http://www.facebook.com/event.php?eid=%s" % self.facebook_eid
    
    def details_url(self):
        return "/event/%s" % self.get_key_name()