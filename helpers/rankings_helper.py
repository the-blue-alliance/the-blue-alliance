from consts.ranking_indexes import RankingIndexes
from models.event_details import EventDetails


class RankingsHelper(object):
    SORT_ORDERS = {
        2016: [2, 3, 4, 5, 6],
        2015: [2, 5, 3, 4, 7, 6],
        2014: [2, 3, 4, 5, 6],
        2013: [2, 3, 4, 5],
        2012: [2, 3, 4, 5],
        2011: [6, 7],
        2010: [3, 4, 5],
        2009: [6, 7, 8],
        2008: [6, 7, 8],
        2007: [6, 7, 8],
    }

    @classmethod
    def migrate_rankings(cls, event_key):
        """
        Converts event_details.rankings to event_details.rankings2
        """
        event_details = EventDetails.get_by_id(event_key)
        year = event_details.year
        if event_key == '2015mttd':  # 2015mttd played the 2014 game
            year = 2014

        # Look up indexes
        mp_index = RankingIndexes.MATCHES_PLAYED.get(year)
        if mp_index is None:
            return
        ranking_index = RankingIndexes.RECORD_INDEXES.get(year)
        dq_index = None

        # Overwrite indexes in case thing are different
        for i, name in enumerate(event_details.rankings[0]):
            name = name.lower()
            if name == 'played':
                mp_index = i
            if name == 'dq':
                dq_index = i

        sort_order_indices = cls.SORT_ORDERS[year]
      # Special case for offseasons with different ordering
        if year == 2015 and event_details.rankings[0][3].lower() == 'coopertition':
            sort_order_indices = [2, 3, 5, 4, 6, 7]

        rankings2 = []
        for row in event_details.rankings[1:]:
            if ranking_index is None:
                record = None
            elif type(ranking_index) == tuple:
                record = {
                    'wins': int(row[ranking_index[0]]),
                    'losses': int(row[ranking_index[1]]),
                    'ties': int(row[ranking_index[2]])
                }
            else:
                wins, losses, ties = row[ranking_index].split('-')
                record = {
                    'wins': int(wins),
                    'losses': int(losses),
                    'ties': int(ties)
                }

            if dq_index is None:
                dq = 0
            else:
                dq = int(row[dq_index])

            if year == 2015:
                qual_average = row[RankingIndexes.CUMULATIVE_RANKING_SCORE.get(year)]
            else:
                qual_average = None

            sort_orders = [float(row[index]) for index in sort_order_indices]

            ranking = {
                'rank': int(row[0]),
                'team_key': 'frc{}'.format(row[1]),
                'record': record,  # None if record doesn't affect rank (e.g. 2010, 2015)
                'qual_average': qual_average,  # None if qual_average doesn't affect rank (all years except 2015)
                'matches_played': row[mp_index],
                'dq': dq,
                'sort_orders': sort_orders,
            }
            rankings2.append(ranking)

        return rankings2
