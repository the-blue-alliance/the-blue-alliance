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
    insights = ndb.JsonProperty()
    predictions = ndb.JsonProperty()
    rankings = ndb.JsonProperty()
    rankings2 = ndb.JsonProperty()

    # Based on the output of PlayoffAdvancementHelper.generatePlayoffAdvancement
    # Dict with keys for: bracket, playoff_advancement
    playoff_advancement = ndb.JsonProperty()

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

        has_extra_stats = False
        if self.rankings2:
            for rank in self.rankings2:
                rank['extra_stats'] = []
                if self.year in {2017, 2018, 2019, 2020}:
                    rank['extra_stats'] = [
                        int(round(rank['sort_orders'][0] * rank['matches_played'])),
                    ]
                    has_extra_stats = True
                elif rank['qual_average'] is None:
                    rank['extra_stats'] = [
                        rank['sort_orders'][0] / rank['matches_played'] if rank['matches_played'] > 0 else 0,
                    ]
                    has_extra_stats = True

        sort_order_info = RankingsHelper.get_sort_order_info(self)
        extra_stats_info = []
        if has_extra_stats:
            if self.year in {2017, 2018, 2019, 2020}:
                extra_stats_info = [{
                    'name': 'Total Ranking Points',
                    'precision': 0,
                }]
            else:
                extra_stats_info = [{
                    'name': '{}/Match'.format(sort_order_info[0]['name']),
                    'precision': 2,
                }]

        return {
            'rankings': self.rankings2,
            'sort_order_info': sort_order_info,
            'extra_stats_info': extra_stats_info,
        }

    @property
    def rankings_table(self):
        if not self.rankings2:
            return None

        rankings = self.renderable_rankings

        precisions = []
        for item in rankings['sort_order_info']:
            precisions.append(item['precision'])

        extra_precisions = []
        for item in rankings['extra_stats_info']:
            extra_precisions.append(item['precision'])

        rankings_table = []
        has_record = False
        for rank in self.rankings2:
            row = [rank['rank'], rank['team_key'][3:]]
            # for i, item in enumerate(rank['sort_orders']):
            for i, precision in enumerate(precisions):
                # row.append('%.*f' % (precisions[i], round(item, precisions[i])))
                row.append('%.*f' % (precision, round(rank['sort_orders'][i], precision)))
            if rank['record']:
                row.append('{}-{}-{}'.format(rank['record']['wins'], rank['record']['losses'], rank['record']['ties']))
                has_record = True
            row.append(rank['dq'])
            row.append(rank['matches_played'])

            for i, precision in enumerate(extra_precisions):
                row.append('%.*f' % (precision, round(rank['extra_stats'][i], precision)))

            rankings_table.append(row)

        title_row = ['Rank', 'Team']
        for item in rankings['sort_order_info']:
            title_row.append(item['name'])
        if has_record:
            title_row += ['Record (W-L-T)']
        title_row += ['DQ', 'Played']

        for item in rankings['extra_stats_info']:
            title_row.append('{}*'.format(item['name']))

        rankings_table = [title_row] + rankings_table
        return rankings_table
