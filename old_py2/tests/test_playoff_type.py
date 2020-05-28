import unittest2

from consts.playoff_type import PlayoffType


class TestPlayoffType(unittest2.TestCase):
    def test_BRACKET_8_TEAM(self):
        playoff_type = PlayoffType.BRACKET_8_TEAM

        # Qual
        for i in xrange(50):
            self.assertEqual(
                PlayoffType.get_comp_level(playoff_type, 'Qualification', i + 1),
                'qm'
            )
            self.assertEqual(
                PlayoffType.get_set_match_number(playoff_type, 'qm', i + 1),
                (1, i + 1)
            )

        # Playoff
        expected = [
            'qf', 'qf', 'qf',
            'qf', 'qf', 'qf',
            'qf', 'qf', 'qf',
            'qf', 'qf', 'qf',
            'sf', 'sf', 'sf',
            'sf', 'sf', 'sf',
            'f', 'f', 'f',
        ]
        for i in xrange(21):
            self.assertEqual(
                PlayoffType.get_comp_level(playoff_type, 'Playoff', i + 1),
                expected[i]
            )

        self.assertEqual(
            PlayoffType.get_set_match_number(playoff_type, 'qf', 1),
            (1, 1)
        )
        self.assertEqual(
            PlayoffType.get_set_match_number(playoff_type, 'qf', 12),
            (4, 3)
        )
        self.assertEqual(
            PlayoffType.get_set_match_number(playoff_type, 'sf', 13),
            (1, 1)
        )
        self.assertEqual(
            PlayoffType.get_set_match_number(playoff_type, 'sf', 18),
            (2, 3)
        )
        self.assertEqual(
            PlayoffType.get_set_match_number(playoff_type, 'f', 19),
            (1, 1)
        )
        self.assertEqual(
            PlayoffType.get_set_match_number(playoff_type, 'f', 21),
            (1, 3)
        )

    def test_ROUND_ROBIN_6_TEAM(self):
        playoff_type = PlayoffType.ROUND_ROBIN_6_TEAM

        # Qual
        for i in xrange(50):
            self.assertEqual(
                PlayoffType.get_comp_level(playoff_type, 'Qualification', i + 1),
                'qm'
            )
            self.assertEqual(
                PlayoffType.get_set_match_number(playoff_type, 'qm', i + 1),
                (1, i + 1)
            )

        # Playoff
        expected = [
            'sf', 'sf', 'sf',
            'sf', 'sf', 'sf',
            'sf', 'sf', 'sf',
            'sf', 'sf', 'sf',
            'sf', 'sf', 'sf',
            'f', 'f', 'f',
        ]
        for i in xrange(18):
            self.assertEqual(
                PlayoffType.get_comp_level(playoff_type, 'Playoff', i + 1),
                expected[i]
            )

        self.assertEqual(
            PlayoffType.get_set_match_number(playoff_type, 'sf', 1),
            (1, 1)
        )
        self.assertEqual(
            PlayoffType.get_set_match_number(playoff_type, 'sf', 15),
            (1, 15)
        )
        self.assertEqual(
            PlayoffType.get_set_match_number(playoff_type, 'f', 16),
            (1, 1)
        )
        self.assertEqual(
            PlayoffType.get_set_match_number(playoff_type, 'f', 18),
            (1, 3)
        )
