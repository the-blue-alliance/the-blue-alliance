import logging

from google.appengine.ext import db

from models.award import Award
#global sort order
sortOrder = [
    'rca',
    'rca1',
    'rca12',
    'ei',
    'ras',
    'rinspire',
    'wfa',
    'vol',
    'dlf',
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
    'coop',
    'create',
    'eng',
    'entre',
    'gp',
    'hrs',
    'image',
    'ind',
    'safe',
    'control',
    'quality',
    'spirit',
    'web',
    'judge',
    'judge2',
]


class AwardHelper(object):
    """
    Helper to prepare awards for being used in a template
    """
    @classmethod
    def organizeAwards(self, award_list):
        awards = dict([(award.name, award) for award in award_list])
        awards['list'] = list()
        for item in sortOrder:
            if awards.has_key(item):
                awards['list'].append(awards[item])
        return awards
