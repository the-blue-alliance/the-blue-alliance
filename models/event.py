from google.appengine.ext import db
import json

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
    webcast_json = db.TextProperty(indexed=False)
    oprs = db.ListProperty(float, indexed=False)
    opr_teams = db.ListProperty(int, indexed=False)
    rankings_json = db.TextProperty(indexed=False)

    def __init__(self, *args, **kw):
        self._rankings = None
        self._webcast = None
        super(Event, self).__init__(*args, **kw)
    
    @property
    def rankings(self):
        """
        Lazy load parsing rankings JSON
        """
        if self._rankings is None:
            if type(self.rankings_json) == db.Text:
                self._rankings = json.loads(self.rankings_json)
            else:
                self._rankings = None
        return self._rankings
    
    @property
    def webcast(self):
        """
        Lazy load parsing webcast JSON
        """
        if self._webcast is None:
            if type(self.webcast_json) == db.Text:
                self._webcast = json.loads(self.webcast_json)
            else:
                self._webcast = None
        return self._webcast

    @property
    def key_name(self):
        """
        Returns the string of the key_name of the Event object before writing it.
        """
        return str(self.year) + self.event_short
    
    @property 
    def facebook_event_url(self):
        """
        Return a string of the Facebook Event URL.
        """
        return "http://www.facebook.com/event.php?eid=%s" % self.facebook_eid
    
    @property
    def details_url(self):
        """
        Returns the URL pattern for the link to this Event on TBA
        """
        return "/event/%s" % self.key_name
