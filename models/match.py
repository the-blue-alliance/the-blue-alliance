import json

from google.appengine.ext import db

from models.event import Event

class Match(db.Model):
    """
    Matches represent individual matches at Events.
    Matches have many Videos.
    Matches have many Alliances.
    key_name is like 2010ct_qm10 or 2010ct_sf1m2
    """
    
    COMP_LEVELS = ["qm", "ef", "qf", "sf", "f"]
    COMP_LEVELS_VERBOSE = {
        "qm": "Quals",
        "ef": "Eighths",
        "qf": "Quarters",
        "sf": "Semis",
        "f": "Finals",
    }
        
    FRC_GAMES = [
        "frc_2012_rebr",
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
        2012: "frc_2012_rebr",
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
    
    alliances_json = db.StringProperty(required=True) #JSON dictionary with alliances and scores.
    
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
    
    comp_level = db.StringProperty(required=True,choices=set(COMP_LEVELS))
    event = db.ReferenceProperty(Event, required=True)
    game = db.StringProperty(required=True,choices=set(FRC_GAMES))
    match_number = db.IntegerProperty(required=True)
    no_auto_update = db.BooleanProperty(default=False) #Set to True after manual update
    set_number = db.IntegerProperty(required=True)
    team_key_names = db.StringListProperty(required=True) #list of teams in Match, for indexing.
    time = db.DateTimeProperty()
    youtube_videos = db.StringListProperty() # list of Youtube IDs
    tba_videos = db.StringListProperty() # list of filetypes a TBA video exists for
    
    def event_key_name(self):
        return Match.event.get_value_for_datastore(self).name()
    
    def get_key_name(self):
        if self.comp_level == "qm":
            return self.event_key_name() + '_qm' + str(self.match_number)
        else:
            return (self.event_key_name() + '_' + self.comp_level +
                str(self.set_number) + 'm' + str(self.match_number))
    
    def unpack_json(self):
        """Turn that JSON into a dict."""
        self.alliances = json.loads(self.alliances_json)
        self.winning_alliance = self.get_winning_alliance()
        # TODO: there's a way to do this lazily as soon as we try to access 
        # something under .alliances., right? -gregmarra 17 Oct 2010
        return ""
    
    def has_been_played(self):
        """If there are scores, it's been played"""
        for alliance in self.alliances:
            if self.alliances[alliance]["score"] is not None:
                return True
        return False
    
    def get_winning_alliance(self):
        highest_score = 0
        winner = ""
        for alliance in self.alliances:
            if int(self.alliances[alliance]["score"]) > highest_score:
                highest_score = int(self.alliances[alliance]["score"])
                winner = alliance
            elif int(self.alliances[alliance]["score"]) == highest_score:
                winner = ""
        return winner
    
    def verbose_name(self):
        if self.comp_level == "qm" or self.comp_level == "f":
            return "%s %s" % (self.COMP_LEVELS_VERBOSE[self.comp_level], self.match_number)
        else:
            return "%s %s Match %s" % (self.COMP_LEVELS_VERBOSE[self.comp_level], self.set_number, self.match_number)
    
    def has_video(self):
        return (len(self.youtube_videos) + len(self.tba_videos)) > 0
    
    def details_url(self):
        return "/match/%s" % self.get_key_name()