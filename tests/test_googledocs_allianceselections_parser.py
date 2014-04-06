import unittest2

from datafeeds.googledocs_allianceselections_parser import GoogleDocsAllianceSelectionsParser


class TestGoogleDocsAllianceSelectionsParser(unittest2.TestCase):
    CASA = {
        1: {
            'declines': [],
            'picks': [
                'frc971',
                'frc1678',
                'frc766'
            ]
        },
        2: {
            'declines': [],
            'picks': [
                'frc2085',
                'frc1671',
                'frc692'
            ]
        },
        3: {
            'declines': [],
            'picks': [
                'frc2761',
                'frc100',
                'frc1662'
            ]
        },
        4: {
            'declines': [],
            'picks': [
                'frc114',
                'frc2035',
                'frc115'
            ]
        },
        5: {
            'declines': [],
            'picks': [
                'frc4159',
                'frc599',
                'frc3250'
            ]
        },
        6: {
            'declines': [],
            'picks': [
                'frc1280',
                'frc4135',
                'frc701'
            ]
        },
        7: {
            'declines': [],
            'picks': [
                'frc668',
                'frc1868',
                'frc2073'
            ]
        },
        8: {
            'declines': [],
            'picks': [
                'frc1388',
                'frc2551',
                'frc2144'
            ]
        }
    }

    def test_parse(self):
        with open('test_data/2014alliance_selection.csv', 'r') as f:
            events = GoogleDocsAllianceSelectionsParser.parse(f.read())
        self.assertEqual(events['casa'], self.CASA)
