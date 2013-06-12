import unittest2

from common.tba_key_name_validators import validate_team_key_name, validate_event_key_name,\
                                          validate_match_key_name
class TestKeyNameValidators(unittest2.TestCase):

    def setUp(self):
        self.valid_team_key = "frc177"
        self.invalid_team_key = "bcr077"

        self.valid_event_key = "2010ct"
        self.invalid_event_key = "210c1"

        self.valid_match_key = "2010ct_sf1m2"
        self.invalid_match_key = "0010c1_0m2"

    def test_valid_team_key(self):
        self.assertEqual(validate_team_key_name(self.valid_team_key), True)

    def test_invalid_team_key(self):
        self.assertEqual(validate_team_key_name(self.invalid_team_key), False)

    def test_valid_event_key(self):
        self.assertEqual(validate_event_key_name(self.valid_event_key), True)

    def test_Invalid_event_key(self):
        self.assertEqual(validate_event_key_name(self.invalid_event_key), False)

    def test_valid_match_key(self):
        self.assertEqual(validate_match_key_name(self.valid_match_key), True)

    def test_invalid_match_key(self):
        self.assertEqual(validate_match_key_name(self.invalid_match_key), False)

if __name__ == '__main__':
    unittest.main()
