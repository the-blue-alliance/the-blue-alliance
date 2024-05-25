import unittest2

from datafeeds.csv_alliance_selections_parser import CSVAllianceSelectionsParser


class TestCSVAllianceSelectionsParser(unittest2.TestCase):
    def test_parse(self):
        with open('test_data/2014casj_alliances.csv', 'r') as f:
            alliances = CSVAllianceSelectionsParser.parse(f.read())

        self.assertEqual(alliances,
                         [{'picks': ['frc971', 'frc254', 'frc1662'], 'declines': []},
                          {'picks': ['frc1678', 'frc368', 'frc4171'], 'declines': []},
                          {'picks': ['frc2035', 'frc192', 'frc4990'], 'declines': []},
                          {'picks': ['frc1323', 'frc846', 'frc2135'], 'declines': []},
                          {'picks': ['frc2144', 'frc1388', 'frc668'], 'declines': []},
                          {'picks': ['frc1280', 'frc604', 'frc100'], 'declines': []},
                          {'picks': ['frc114', 'frc852', 'frc841'], 'declines': []},
                          {'picks': ['frc2473', 'frc3256', 'frc1868'], 'declines': []}])
