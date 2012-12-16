import json
from google.appengine.ext import ndb

class Insight(ndb.Model):
    """
    Insights are the end result of analyzing a batch of data, such as the
    average score for all matches in a year.
    key_name is like '2012insights_matchavg'
    """
        
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
        Lazy load data_json
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
        if year == 0:
            return 'insights' + '_' + str(name)
        else:
            return str(year) + 'insights' + '_' + str(name)
