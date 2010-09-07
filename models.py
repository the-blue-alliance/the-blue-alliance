from google.appengine.ext import db

from django.utils import simplejson

class Team(db.Model):
    """
    Teams represent FIRST Robotics Competition teams.
    key_name is like 'frc177'
    """
    team_number = db.IntegerProperty(required=True)
    name = db.StringProperty()
    nickname = db.StringProperty()
    address = db.PostalAddressProperty()
    website = db.LinkProperty()
    first_tpid = db.IntegerProperty() #from USFIRST. FIRST team ID number. -greg 5/20/2010


class Event(db.Model):
    """
    Events represent FIRST Robotics Competition events, both official and unofficial.
    key_name is like '2010ct'
    """
    name = db.StringProperty()
    event_type = db.StringProperty() # From USFIRST
    short_name = db.StringProperty() # Should not contain "Regional" or "Division", like "Hartford"
    event_short = db.StringProperty(required=True) # Smaller abbreviation like "CT"
    year = db.IntegerProperty(required=True)
    start_date = db.DateTimeProperty()
    end_date = db.DateTimeProperty()
    venue = db.StringProperty()
    venue_address = db.PostalAddressProperty() # We can scrape this.
    location = db.StringProperty()
    official = db.BooleanProperty(default=False) # Is the event FIRST-official?
    first_eid = db.StringProperty() #from USFIRST
    website = db.StringProperty()
    
    def get_key_name(self):
        """
        Returns the string of the key_name of the Event object.
        """
        return str(self.year) + self.event_short


class EventTeam(db.Model):
    """
    EventTeam serves as a join model between Events and Teams, indicating that
    a team will or has competed in an Event.
    """
    event = db.ReferenceProperty(Event,
                                 collection_name='teams')
    team = db.ReferenceProperty(Team,
                                collection_name='events')


class Match(db.Model):
    """
    Matches represent individual matches at Events.
    Matches have many Videos.
    Matches have many Alliances.
    key_name is like 2010ct_qm10 or 2010ct_sf1m2
    """
    
    COMP_LEVELS = ["qm", "qf", "sf", "f"]
        
    FRC_GAMES = [
        "frc_2010_bkwy",
        "frc_2009_lncy",
        "frc_2008_ovdr",
        "frc_2007_rkrl",
        "frc_2006_amhi",
        "frc_2005_trpl",
        "frc_2004_frnz",
        "frc_2003_stck",
        "frc_2002_znzl",
        "frc_2001_dbdy",
        "frc_2000_coop",
        "frc_1999_trbl",
        "frc_1998_lddr",
        "frc_1997_trdt",
        "frc_1996_hxgn",
        "frc_1995_rmpr",
        "frc_1994_tpwr",
        "frc_1993_rgrg",
        "frc_1992_maiz",
        "frc_unknown",
    ]
    
    game = db.StringProperty(required=True,choices=set(FRC_GAMES))
    
    event = db.ReferenceProperty(Event, required=True)
    time = db.DateTimeProperty()
    
    comp_level = db.StringProperty(required=True,choices=set(COMP_LEVELS))
    set_number = db.IntegerProperty(required=True)
    match_number = db.IntegerProperty(required=True)
    
    team_key_names = db.StringListProperty(required=True) #list of teams in Match, for indexing.
    alliances_json = db.StringProperty(required=True) #JSON dictionary with alliances and scores.
    
    no_auto_update = db.BooleanProperty(default=False) #Set to True after manual update
    
    # {
    # "red": {
    #    "teams": ["frc177", "frc195", "frc125"], # These are Team keys
    #    "score": 25
    # },
    # "blue": {
    #    "teams": ["frc433", "frc254", "frc222"],
    #    "score": 12
    # }
    # }
    
    def get_key_name(self):
        if self.comp_level == "qm":
            return self.event.get_key_name() + '_qm' + str(self.match_number)
        else:
            return (self.event.get_key_name() + '_' + self.comp_level +
                str(self.set_number) + 'm' + str(self.match_number))


# TODO: Make Video subclasses inherit from an Interface class.
class TBAVideo(db.Model):
    """
    Store information related to videos of Matches hosted on
    The Blue Alliance.
    """
    match = db.ReferenceProperty(Match,
                                 required=True)
    location = db.StringProperty()


class YoutubeVideo(db.Model):
    """
    Store information related to videos of Matches hosted on YouTube.
    """
    match = db.ReferenceProperty(Match,
                                 required=True)
    youtube_id = db.StringProperty()