import unittest2

from models.event import Event
from models.match import Match
from models.team import Team


class TestKeyNameValidators(unittest2.TestCase):
    def setUp(self):
        self.valid_team_key = "frc177"
        self.valid_team_key2 = "frc1"
        self.invalid_team_key = "bcr077"
        self.invalid_team_key2 = "frc 011"
        self.invalid_team_key3 = "frc711\\"

        self.valid_event_key = "2010ct"
        self.valid_event_key2 = "2014onto2"
        self.invalid_event_key = "210c1"
        self.invalid_event_key2 = "frc2010ct"
        self.invalid_event_key3 = "2010 ct"

        self.valid_match_key = "2010ct_sf1m2"
        self.invalid_match_key = "0010c1_0m2"
        self.invalid_match_key2 = "2010c1_1f1m1"
        self.invalid_match_key3 = "2010c1_ef10m1"

    def test_valid_team_key(self):
        self.assertEqual(Team.validate_key_name(self.valid_team_key), True)
        self.assertEqual(Team.validate_key_name(self.valid_team_key2), True)

    def test_invalid_team_key(self):
        self.assertEqual(Team.validate_key_name(self.invalid_team_key), False)
        self.assertEqual(Team.validate_key_name(self.invalid_team_key2), False)
        self.assertEqual(Team.validate_key_name(self.invalid_team_key3), False)

    def test_valid_event_key(self):
        self.assertEqual(Event.validate_key_name(self.valid_event_key), True)
        self.assertEqual(Event.validate_key_name(self.valid_event_key2), True)

    def test_invalid_event_key(self):
        self.assertEqual(Event.validate_key_name(self.invalid_event_key), False)
        self.assertEqual(Event.validate_key_name(self.invalid_event_key2), False)
        self.assertEqual(Event.validate_key_name(self.invalid_event_key3), False)

    def test_valid_match_key(self):
        self.assertEqual(Match.validate_key_name(self.valid_match_key), True)

    def test_invalid_match_key(self):
        self.assertEqual(Match.validate_key_name(self.invalid_match_key), False)
        self.assertEqual(Match.validate_key_name(self.invalid_match_key2), False)
        self.assertEqual(Match.validate_key_name(self.invalid_match_key3), False)

if __name__ == '__main__':
    unittest.main()
