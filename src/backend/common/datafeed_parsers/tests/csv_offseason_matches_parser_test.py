import json
import unittest

from backend.common.datafeed_parsers.csv_offseason_matches_parser import (
    CSVOffseasonMatchesParser,
)


class TestCSVOffseasonMatchesParser(unittest.TestCase):
    def test_parse_empty(self) -> None:
        matches, more_results = CSVOffseasonMatchesParser.parse("")
        self.assertEqual(matches, [])
        self.assertFalse(more_results)

    def test_parse_qual_match(self) -> None:
        csv = "qm1,254,1114,2056,148,217,118,55,40\n"
        matches, more_results = CSVOffseasonMatchesParser.parse(csv)
        self.assertFalse(more_results)
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(
            match["team_key_names"],
            ["frc254", "frc1114", "frc2056", "frc148", "frc217", "frc118"],
        )
        self.assertEqual(
            json.loads(match["alliances_json"]),
            {
                "red": {"teams": ["frc254", "frc1114", "frc2056"], "score": 55},
                "blue": {"teams": ["frc148", "frc217", "frc118"], "score": 40},
            },
        )

    def test_parse_multiple_rows_and_levels(self) -> None:
        csv = (
            "qm12,1,2,3,4,5,6,10,20\n"
            "qf3m1,1,2,3,4,5,6,0,2\n"
            "sf2m3,1,2,3,4,5,6,7,7\n"
            "f1m2,1,2,3,4,5,6,10,9\n"
        )
        matches, _ = CSVOffseasonMatchesParser.parse(csv)
        self.assertEqual(
            [(m["comp_level"], m["set_number"], m["match_number"]) for m in matches],
            [("qm", 1, 12), ("qf", 3, 1), ("sf", 2, 3), ("f", 1, 2)],
        )

    def test_parse_skips_leading_whitespace_after_delimiter(self) -> None:
        csv = "qm1, 254, 1114, 2056, 148, 217, 118, 55, 40"
        matches, _ = CSVOffseasonMatchesParser.parse(csv)
        self.assertEqual(
            matches[0]["team_key_names"],
            ["frc254", "frc1114", "frc2056", "frc148", "frc217", "frc118"],
        )
        alliances = json.loads(matches[0]["alliances_json"])
        self.assertEqual(alliances["red"]["score"], 55)
        self.assertEqual(alliances["blue"]["score"], 40)

    def test_parse_match_id_surrounding_whitespace_is_stripped(self) -> None:
        matches, _ = CSVOffseasonMatchesParser.parse(" qf3m1 ,1,2,3,4,5,6,0,2")
        self.assertEqual(matches[0]["comp_level"], "qf")
        self.assertEqual(matches[0]["set_number"], 3)
        self.assertEqual(matches[0]["match_number"], 1)

    def test_parse_missing_scores_become_negative_one(self) -> None:
        matches, _ = CSVOffseasonMatchesParser.parse("qm1,1,2,3,4,5,6,,")
        alliances = json.loads(matches[0]["alliances_json"])
        self.assertEqual(alliances["red"]["score"], -1)
        self.assertEqual(alliances["blue"]["score"], -1)

    def test_parse_zero_score_is_kept(self) -> None:
        # "0" is truthy as a string, so a real zero must survive as 0, not -1
        matches, _ = CSVOffseasonMatchesParser.parse("qm1,1,2,3,4,5,6,0,0")
        alliances = json.loads(matches[0]["alliances_json"])
        self.assertEqual(alliances["red"]["score"], 0)
        self.assertEqual(alliances["blue"]["score"], 0)

    def test_parse_non_numeric_team_is_uppercased_and_not_a_team_key(self) -> None:
        matches, _ = CSVOffseasonMatchesParser.parse("qm1,254,2056b,x,148,217,118,1,2")
        alliances = json.loads(matches[0]["alliances_json"])
        self.assertEqual(alliances["red"]["teams"], ["frc254", "frc2056B", "frcX"])
        # Only purely numeric teams become team_key_names
        self.assertEqual(
            matches[0]["team_key_names"], ["frc254", "frc148", "frc217", "frc118"]
        )

    def test_parse_csv_match_strips_row_in_place(self) -> None:
        row = [" qm1", "254 ", "1114", "2056", "148", "217", "118", "1", "2"]
        CSVOffseasonMatchesParser.parse_csv_match(row)
        self.assertEqual(
            row, ["qm1", "254", "1114", "2056", "148", "217", "118", "1", "2"]
        )

    def test_parse_csv_match_wrong_column_count(self) -> None:
        with self.assertRaises(ValueError):
            CSVOffseasonMatchesParser.parse_csv_match(["qm1", "1", "2"])

    def test_parse_match_number_info(self) -> None:
        self.assertEqual(
            CSVOffseasonMatchesParser.parse_match_number_info("qm7"), ("qm", 7, 1)
        )
        self.assertEqual(
            CSVOffseasonMatchesParser.parse_match_number_info("ef4m2"), ("ef", 2, 4)
        )
        self.assertEqual(
            CSVOffseasonMatchesParser.parse_match_number_info("qf1m3"), ("qf", 3, 1)
        )
        self.assertEqual(
            CSVOffseasonMatchesParser.parse_match_number_info("sf2m1"), ("sf", 1, 2)
        )
        self.assertEqual(
            CSVOffseasonMatchesParser.parse_match_number_info(" f1m2 "), ("f", 2, 1)
        )

    def test_parse_match_number_info_unknown_level(self) -> None:
        with self.assertRaises(KeyError):
            CSVOffseasonMatchesParser.parse_match_number_info("xx1")

    def test_parse_elim_match_number_info_two_digit_set(self) -> None:
        """"sf12m1" is set 12, match 1."""
        self.assertEqual(
            CSVOffseasonMatchesParser.parse_elim_match_number_info("sf12m1"), (1, 12)
        )
        self.assertEqual(
            CSVOffseasonMatchesParser.parse_match_number_info("sf12m1"), ("sf", 1, 12)
        )

    def test_parse_elim_match_number_info_requires_set_number(self) -> None:
        # An elim id without a set number ("fm1") is rejected. Today that is a
        # ValueError from int("f"), since COMP_LEVEL_MAP happens to accept
        # "fm"; a KeyError for the unknown level would be just as correct.
        with self.assertRaises((KeyError, ValueError)):
            CSVOffseasonMatchesParser.parse_match_number_info("fm1")
        with self.assertRaises((KeyError, ValueError)):
            CSVOffseasonMatchesParser.parse_match_number_info("efm2")

    def test_parse_qual_match_number_info(self) -> None:
        self.assertEqual(
            CSVOffseasonMatchesParser.parse_qual_match_number_info("qm42"), (42, 1)
        )
