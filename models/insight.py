import json
from google.appengine.ext import ndb

class Insight(ndb.Model):
    """
    Insights are the end result of analyzing a batch of data, such as the
    average score for all matches in a year.
    key_name is like '2012insights_matchavg'
    """
    
    MATCH_HIGHSCORE = 0
    MATCH_AVERAGES = 1
    BUCKETED_SCORES = 2
    REGIONAL_DISTRICT_WINNERS = 3
    DIVISION_FINALISTS = 4
    DIVISION_WINNERS = 5
    WORLD_FINALISTS = 6
    WORLD_CHAMPIONS = 7
    RCA_WINNERS = 8
    CA_WINNER = 9
    BLUE_BANNERS = 10
    NUM_MATCHES = 11
    ELIM_MATCH_AVERAGES = 12
    ELIM_BUCKETED_SCORES = 13
    
    # Used for datastore keys! Don't change unless you know what you're doing.
    INSIGHT_NAMES = {MATCH_HIGHSCORE: 'match_highscore',
                     BUCKETED_SCORES: 'bucketed_scores',
                     REGIONAL_DISTRICT_WINNERS: 'regional_district_winners',
                     DIVISION_FINALISTS: 'division_finalists',
                     DIVISION_WINNERS: 'division_winners',
                     WORLD_FINALISTS: 'world_finalists',
                     WORLD_CHAMPIONS: 'world_champions',
                     RCA_WINNERS: 'rca_winners',
                     CA_WINNER: 'ca_winner',
                     BLUE_BANNERS: 'blue_banners',
                     MATCH_AVERAGES: 'match_averages',
                     NUM_MATCHES: 'num_matches',
                     ELIM_MATCH_AVERAGES: 'elim_match_averages',
                     ELIM_BUCKETED_SCORES: 'elim_bucketed_scores',
                     }
        
    name = ndb.StringProperty(required=True)  # general name used for sorting
    year = ndb.IntegerProperty(required=True) # year this insight pertains to. year = 0 for overall insights
    data_json = ndb.StringProperty(required=True, indexed=False)  # JSON dictionary of the data of the insight

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)
    
    def __init__(self, *args, **kw):
      self._data = None
      super(Insight, self).__init__(*args, **kw)

    @property
    def data(self):
        """
        Lazy load data_json as an OrderedDict
        """
        if self._data is None:
            self._data = json.loads(self.data_json)
        return self._data
    
    @property
    def key_name(self):
        """
        Returns the string of the key_name of the Insight object before writing it.
        """
        return self.renderKeyName(self.year, self.name)

    @classmethod
    def renderKeyName(self, year, name):
        if year == None:
            return 'insights' + '_' + str(name)
        else:
            return str(year) + 'insights' + '_' + str(name)
