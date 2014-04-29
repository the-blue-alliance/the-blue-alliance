import unittest2

from datafeeds.usfirst_alliances_parser import UsfirstAlliancesParser


class TestUsfirstAlliancesParser(unittest2.TestCase):
    def test_parse_2014test(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2014test.html', 'r') as f:
            alliances, _ = UsfirstAlliancesParser.parse(f.read())

        self.assertEqual(alliances, None)

    def test_parse_2014curie(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2014curie.html', 'r') as f:
            alliances, _ = UsfirstAlliancesParser.parse(f.read())

        self.assertEqual(
            alliances,
            {
                1: {'picks': ['frc254', 'frc469', 'frc2848', 'frc74'], 'declines':[] },
                2: {'picks': ['frc1718', 'frc2451', 'frc573', 'frc2016'], 'declines':[] },
                3: {'picks': ['frc2928', 'frc2013', 'frc1311', 'frc842'], 'declines':[] },
                4: {'picks': ['frc180', 'frc125', 'frc1323', 'frc2468'], 'declines':[] },
                5: {'picks': ['frc118', 'frc359', 'frc4334', 'frc865'], 'declines':[] },
                6: {'picks': ['frc135', 'frc1241', 'frc11', 'frc68'], 'declines':[] },
                7: {'picks': ['frc3478', 'frc177', 'frc294', 'frc230'], 'declines':[] },
                8: {'picks': ['frc624', 'frc987', 'frc3476', 'frc3015'], 'declines':[] },
            }
        )
