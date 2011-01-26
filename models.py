import logging

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
    first_tpid_year = db.IntegerProperty() # from USFIRST. Year tpid is applicable for. -greg 9 Jan 2011


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
        Returns the string of the key_name of the Event object before writing it.
        """
        return str(self.year) + self.event_short


class EventTeam(db.Model):
    """
    EventTeam serves as a join model between Events and Teams, indicating that
    a team will or has competed in an Event.
    key_name is like 2010cmp_frc177 or 2007ct_frc195
    """
    event = db.ReferenceProperty(Event,
                                 collection_name='teams')
    team = db.ReferenceProperty(Team,
                                collection_name='events')
    year = db.IntegerProperty()


class Match(db.Model):
    """
    Matches represent individual matches at Events.
    Matches have many Videos.
    Matches have many Alliances.
    key_name is like 2010ct_qm10 or 2010ct_sf1m2
    """
    
    COMP_LEVELS = ["qm", "ef", "qf", "sf", "f"]
    COMP_LEVELS_VERBOSE = {
        "qm": "Qualifications",
        "ef": "Eighths",
        "qf": "Quarters",
        "sf": "Semis",
        "f": "Finals",
    }
        
    FRC_GAMES = [
        "frc_2011_logo",
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
    
    FRC_GAMES_BY_YEAR = {
        2011: "frc_2011_logo",
        2010: "frc_2010_bkwy",
        2009: "frc_2009_lncy",
        2008: "frc_2008_ovdr",
        2007: "frc_2007_rkrl",
        2006: "frc_2006_amhi",
        2005: "frc_2005_trpl",
        2004: "frc_2004_frnz",
        2003: "frc_2003_stck",
        2002: "frc_2002_znzl",
        2001: "frc_2001_dbdy",
        2000: "frc_2000_coop",
        1999: "frc_1999_trbl",
        1998: "frc_1998_lddr",
        1997: "frc_1997_trdt",
        1996: "frc_1996_hxgn",
        1995: "frc_1995_rmpr",
        1994: "frc_1994_tpwr",
        1993: "frc_1993_rgrg",
        1992: "frc_1992_maiz",
    }
    
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
    
    def unpack_json(self):
        """Turn that JSON into a dict."""
        self.alliances = simplejson.loads(self.alliances_json)
        self.winning_alliance = self.get_winning_alliance()
        # TODO: there's a way to do this lazily as soon as we try to access 
        # something under .alliances., right? -gregmarra 17 Oct 2010
        return ""
    
    def get_winning_alliance(self):
        highest_score = 0
        winner = ""
        for alliance in self.alliances:
            if int(self.alliances[alliance]["score"]) > highest_score:
                highest_score = int(self.alliances[alliance]["score"])
                winner = alliance
        return winner
    
    def verbose_name(self):
        if self.comp_level == "qm" or self.comp_level == "f":
            return "%s %s" % (self.COMP_LEVELS_VERBOSE[self.comp_level], self.match_number)
        else:
            return "%s %s Match %s" % (self.COMP_LEVELS_VERBOSE[self.comp_level], self.set_number, self.match_number)


class TBAVideo(db.Model):
    """
    Store information related to videos of Matches hosted on 
    videos.thebluealliance.net. Generally, there should only be one
    TBAVideo per match
    """
    
    match = db.ReferenceProperty(Match, required=True)
    filetypes = db.StringListProperty() # ["mp4", "flv", "wmv"] etc
    
    TBA_NET_VID_PATTERN = "http://www.thebluealliance.net/tbatv/vids/%s/%s.%s"
    
    THUMBNAIL_FILETYPES = ["jpg", "jpeg"]
    STREAMABLE_FILETYPES = ["mp4", "flv"]
    DOWNLOADABLE_FILETYPES = ["mp4", "mov", "avi", "wmv"]
    
    def getThumbnailPath(self):
        logging.info("thumbnail: " + self.getBestPathOf(self.THUMBNAIL_FILETYPES))
        return self.getBestPathOf(self.THUMBNAIL_FILETYPES)

    def getStreamablePath(self):
        return self.getBestPathOf(self.STREAMABLE_FILETYPES)
    
    def getDownloadablePath(self):
        return self.getBestPathOf(self.DOWNLOADABLE_FILETYPES)

    def getBestPathOf(self, consider_filetypes):
        for filetype in consider_filetypes:
            if filetype in self.filetypes:
                return self.TBA_NET_VID_PATTERN % (self.match.event.key().name()[2:], self.match.key().name()[4:], filetype)
        return None


class YoutubeVideo(db.Model):
    """
    Store information related to videos of Matches hosted on YouTube.
    """
    match = db.ReferenceProperty(Match, required=True)
    youtube_id = db.StringProperty()

