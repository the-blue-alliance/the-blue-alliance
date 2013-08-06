import logging
from models.award import Award

from google.appengine.ext import db

# Prioritized sort order for certain awards
sortOrder = [
    'cmp_ca',
    'cmp_founders',
    'cmp_ei',
    'cmp_ras',
    'cmp_wfa',
    'cmp_vol',
    'cmp_dl',
    'cmp_dl1',
    'cmp_dl2',
    'cmp_dl3',
    'cmp_dl4',
    'cmp_dl5',
    'cmp_dl6',
    'cmp_dl7',
    'cmp_dl8',
    'cmp_dl9',
    'cmp_win1',
    'cmp_win2',
    'cmp_win3',
    'cmp_win4',
    'cmp_fin1',
    'cmp_fin2',
    'cmp_fin3',
    'cmp_fin4',
    'div_win1',
    'div_win2',
    'div_win3',
    'div_win4',
    'div_fin1',
    'div_fin2',
    'div_fin3',
    'div_fin4',
    'ca',
    'ca1',
    'ca2',
    'ei',
    'ras',
    'wfa',
    'vol',
    'dl',
    'dl1',
    'dl2',
    'dl3',
    'dl4',
    'dl5',
    'dl6',
    'win1',
    'win2',
    'win3',
    'win4',
    'fin1',
    'fin2',
    'fin3',
    'fin4',
    ]

class AwardHelper(object):
    """
    Helper to prepare awards for being used in a template
    awards['list'] is sorted by sortOrder and then the rest
    in alphabetical order by official name
    """

    @classmethod
    def organizeAwards(self, award_list):
        awards = dict([(award.name, award) for award in award_list])
        awards_set = set(awards)

        awards['list'] = list()
        defined_set = set()
        for item in sortOrder:
            if awards.has_key(item):
                awards['list'].append(awards[item])
                defined_set.add(item)

        difference = awards_set.difference(defined_set)
        remaining_awards = []
        for item in difference:
            remaining_awards.append(awards[item])
        remaining_awards = sorted(remaining_awards, key=lambda award: award.official_name)

        awards['list'] += remaining_awards
        return awards

    @classmethod
    def getAwards(self, keys, year=None):
        awards = []
        for key in keys:
            if year == None:
                awards += Award.query(Award.name == key)
            else:
                awards += Award.query(Award.name == key, Award.year == year)
        return awards
