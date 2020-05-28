import unittest2

from helpers.validation_helper import ValidationHelper


class TestValidationHelper(unittest2.TestCase):
    def test_team_validation(self):
        errors = ValidationHelper.validate([("team_id_validator", "frc01")])
        self.assertEqual(errors, {"Errors": [{"team_id": "frc01 is not a valid team id"}]})

    def test_event_validation(self):
        errors = ValidationHelper.validate([("event_id_validator", "1cmp")])
        self.assertEqual(errors, {"Errors": [{"event_id": "1cmp is not a valid event id"}]})

    def test_match_validation(self):
        errors = ValidationHelper.validate([("match_id_validator", "0010c1_0m2")])
        self.assertEqual(errors, {"Errors": [{"match_id": "0010c1_0m2 is not a valid match id"}]})

    def test_michigan_eigth_finals_valid_validation(self):
        errors = ValidationHelper.validate([("match_id_validator", "2015micmp_ef3m1")])
        self.assertEqual(None, errors)

    def test_multi_digits_in_event_key(self):
        errors = ValidationHelper.validate([("event_id_validator", "2017bc18")])
        self.assertEqual(None, errors)

    def test_combo_validation(self):
        errors = ValidationHelper.validate([("match_id_validator", "0010c1_0m2"),
                                            ("team_id_validator", "frc01"),
                                            ("event_id_validator", "1cmp")])
        self.assertEqual(errors, {"Errors": [{"match_id": "0010c1_0m2 is not a valid match id"}, {"team_id": "frc01 is not a valid team id"}, {"event_id": "1cmp is not a valid event id"}]})

    def test_valid_validation(self):
        errors = ValidationHelper.validate([("team_id_validator", "frc101")])
        self.assertEqual(None, errors)
