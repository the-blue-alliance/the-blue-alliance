from google.appengine.ext import ndb


class EventDetails(ndb.Model):
    """
    EventsDetails contains aggregate details about an event that tends to
    update often throughout an event. This includes rankings, event stats, etc.
    key_name is the event key, like '2010ct'
    """
    alliance_selections = ndb.JsonProperty()  # Formatted as: [{'picks': [captain, pick1, pick2, 'frc123', ...], 'declines':[decline1, decline2, ...] }, {'picks': [], 'declines': []}, ... ]
    district_points = ndb.JsonProperty()
    matchstats = ndb.JsonProperty()  # for OPR, DPR, CCWM, etc.
    predictions = ndb.JsonProperty()
    rankings = ndb.JsonProperty()
    rankings2 = ndb.JsonProperty()

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            'key': set(),
        }
        super(EventDetails, self).__init__(*args, **kw)

    def key_name(self):
        return self.key.id()

    @property
    def year(self):
        return int(self.key.id()[:4])

    @property
    def renderable_rankings(self):
        from helpers.rankings_helper import RankingsHelper
        return {
            'rankings': self.rankings2,
            'sort_order_info': RankingsHelper.get_sort_order_info(self),
        }

    @property
    def rankings_table(self):
        from helpers.rankings_helper import RankingsHelper

        precisions = []
        for item in RankingsHelper.get_sort_order_info(self):
            precisions.append(item['precision'])

        rankings_table = []
        has_record = False
        for rank in self.rankings2:
            row = [rank['rank'], rank['team_key'][3:]]
            for i, item in enumerate(rank['sort_orders']):
                row.append('%.*f' % (precisions[i], round(item, precisions[i])))
            if rank['record']:
                row.append('{}-{}-{}'.format(rank['record']['wins'], rank['record']['losses'], rank['record']['ties']))
                has_record = True
            row.append(rank['dq'])
            row.append(rank['matches_played'])
            row.append('%.*f' % (2, round(rank['sort_orders'][0] / rank['matches_played'], 2)))
            rankings_table.append(row)

        title_row = ['Rank', 'Team']
        sort_order_info = RankingsHelper.get_sort_order_info(self)
        for item in sort_order_info:
            title_row.append(item['name'])
        if has_record:
            title_row += ['Record (W-L-T)']
        title_row += ['DQ', 'Played', '{}/Match*'.format(sort_order_info[0]['name'])]

        rankings_table = [title_row] + rankings_table
        return rankings_table
