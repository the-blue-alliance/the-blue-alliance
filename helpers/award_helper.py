import logging

from google.appengine.ext import db

# Prioritized sort order for certain awards
sortOrder = [
    'rca',
    'rca1',
    'rca2',
    'ei',
    'ras',
    'wfa',
    'vol',
    'dlf',
    'dlf1',
    'dlf2',
    'dlf3',
    'dlf4',
    'dlf5',
    'dlf6',
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
