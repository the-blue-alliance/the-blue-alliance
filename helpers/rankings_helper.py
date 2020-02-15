import logging

from consts.ranking_indexes import RankingIndexes
from models.event_details import EventDetails


class RankingsHelper(object):
    SORT_ORDERS = {
        2020: [2, 3, 4, 5, 6],
        2019: [2, 3, 4, 5, 6],
        2018: [2, 3, 4, 5, 6],
        2017: [2, 3, 4, 5, 6, 7],
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

    SORT_ORDER_INFO = {
        2020: [
            {'name': 'Ranking Score',
             'precision': 2},
            {'name': 'Auto',
             'precision': 0},
            {'name': 'End Game',
             'precision': 0},
            {'name': 'Teleop Cell + CPanel',
             'precision': 0}],
        2019: [
            {'name': 'Ranking Score',
             'precision': 2},
            {'name': 'Cargo',
             'precision': 0},
            {'name': 'Hatch Panel',
             'precision': 0},
            {'name': 'HAB Climb',
             'precision': 0},
            {'name': 'Sandstorm Bonus',
             'precision': 0}],
        2018: [
            {'name': 'Ranking Score',
             'precision': 2},
            {'name': 'Park/Climb Points',
             'precision': 0},
            {'name': 'Auto',
             'precision': 0},
            {'name': 'Ownership',
             'precision': 0},
            {'name': 'Vault',
             'precision': 0}],
        2017: [
            {'name': 'Ranking Score',
             'precision': 2},
            {'name': 'Match Points',
             'precision': 0},
            {'name': 'Auto',
             'precision': 0},
            {'name': 'Rotor',
             'precision': 0},
            {'name': 'Touchpad',
             'precision': 0},
            {'name': 'Pressure',
             'precision': 0}],
        2016: [
            {'name': 'Ranking Score',
             'precision': 0},
            {'name': 'Auto',
             'precision': 0},
            {'name': 'Scale/Challenge',
             'precision': 0},
            {'name': 'Goals',
             'precision': 0},
            {'name': 'Defense',
             'precision': 0}],
        2015: [
            {'name': 'Qual Avg.',
             'precision': 1},
            {'name': 'Coopertition',
             'precision': 0},
            {'name': 'Auto',
             'precision': 0},
            {'name': 'Container',
             'precision': 0},
            {'name': 'Tote',
             'precision': 0},
            {'name': 'Litter',
             'precision': 0}],
        2014: [
            {'name': 'Qual Score',
             'precision': 0},
            {'name': 'Assist',
             'precision': 0},
            {'name': 'Auto',
             'precision': 0},
            {'name': 'Truss & Catch',
             'precision': 0},
            {'name': 'Teleop',
             'precision': 0}],
        2013: [
            {'name': 'Qual Score',
             'precision': 0},
            {'name': 'Auto',
             'precision': 0},
            {'name': 'Climb',
             'precision': 0},
            {'name': 'Teleop',
             'precision': 0}],
        2012: [
            {'name': 'Qual Score',
             'precision': 0},
            {'name': 'Hybrid',
             'precision': 0},
            {'name': 'Bridge',
             'precision': 0},
            {'name': 'Teleop',
             'precision': 0}],
        2011: [
            {'name': 'Qual Score',
             'precision': 0},
            {'name': 'Ranking Score',
             'precision': 2}],
        2010: [
            {'name': 'Seeding Score',
             'precision': 0},
            {'name': 'Coopertition Bonus',
             'precision': 0},
            {'name': 'Hanging Points',
             'precision': 0}],
        2009: [
            {'name': 'Qual Score',
             'precision': 0},
            {'name': 'Seeding Score',
             'precision': 2},
            {'name': 'Match Points',
             'precision': 0}],
        2008: [
            {'name': 'Qual Score',
             'precision': 0},
            {'name': 'Seeding Score',
             'precision': 2},
            {'name': 'Match Points',
             'precision': 0}],
        2007: [
            {'name': 'Qual Score',
             'precision': 0},
            {'name': 'Seeding Score',
             'precision': 2},
            {'name': 'Match Points',
             'precision': 0}],
        2006: [
            {'name': 'Qual Score',
             'precision': 0},
            {'name': 'Seeding Score',
             'precision': 2},
            {'name': 'Match Points',
             'precision': 0}],
    }

    NO_RECORD_YEARS = {2010, 2015}

    QUAL_AVERAGE_YEARS = {2015}

    @classmethod
    def build_ranking(cls, year, rank, team_key, wins, losses, ties, qual_average, matches_played, dq, sort_orders):
        if year in cls.NO_RECORD_YEARS:
            record = None
        else:
            record = {
                'wins': int(wins),
                'losses': int(losses),
                'ties': int(ties),
            }

        if year not in cls.QUAL_AVERAGE_YEARS:
            qual_average = None
        else:
            qual_average = float(qual_average)

        sort_orders_sanitized = []
        for so in sort_orders:
            try:
                sort_orders_sanitized.append(float(so))
            except:
                sort_orders_sanitized.append(0.0)

        return {
                'rank': int(rank),
                'team_key': team_key,
                'record': record,  # None if record doesn't affect rank (e.g. 2010, 2015)
                'qual_average': qual_average,  # None if qual_average doesn't affect rank (all years except 2015)
                'matches_played': int(matches_played),
                'dq': int(dq),
                'sort_orders': sort_orders_sanitized,
            }

    @classmethod
    def get_sort_order_info(cls, event_details):
        year = event_details.year
        if event_details.key.id() == '2015mttd':  # 2015mttd played the 2014 game
            year = 2014
        return cls.SORT_ORDER_INFO.get(year)

    @classmethod
    def convert_rankings(cls, event_details):
        """
        Converts event_details.rankings to event_details.rankings2
        """
        if not event_details.rankings:
            return None

        year = event_details.year
        if event_details.key.id() == '2015mttd':  # 2015mttd played the 2014 game
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
                wins = 0
                losses = 0
                ties = 0
            elif type(ranking_index) == tuple:
                wins = row[ranking_index[0]]
                losses = row[ranking_index[1]]
                ties = row[ranking_index[2]]
            else:
                wins, losses, ties = row[ranking_index].split('-')

            if dq_index is None:
                dq = 0
            else:
                dq = int(row[dq_index])

            if year == 2015:
                qual_average = row[RankingIndexes.CUMULATIVE_RANKING_SCORE.get(year)]
            else:
                qual_average = None

            sort_orders = [row[index] for index in sort_order_indices]

            rankings2.append(cls.build_ranking(
                year, int(row[0]), 'frc{}'.format(row[1]), wins, losses, ties, qual_average, row[mp_index], dq, sort_orders))

        return rankings2
