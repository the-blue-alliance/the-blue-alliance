"""Keep the public team playoff schema aligned with fields returned by the API."""

import json
import unittest
from pathlib import Path

SPEC = (
    Path(__file__).resolve().parents[4]
    / "backend"
    / "web"
    / "static"
    / "swagger"
    / "api_v3.json"
)


class TeamEventStatusSchemaTest(unittest.TestCase):
    def test_documented_playoff_fields_bump_patch_version_and_changelog(self) -> None:
        info = json.loads(SPEC.read_text())["info"]
        self.assertEqual(info["version"], "3.27.1")
        self.assertTrue(
            info["x-changes"].startswith(
                "3.27.1: Document playoff_type and double_elim_round in "
                "Team_Event_Status_playoff. "
            )
        )

    def test_playoff_fields_match_wire_types_and_remain_optional(self) -> None:
        schemas = json.loads(SPEC.read_text())["components"]["schemas"]
        playoff = schemas["Team_Event_Status_playoff"]
        properties = playoff["properties"]

        self.assertEqual(
            properties["playoff_type"]["oneOf"],
            [
                {"$ref": "#/components/schemas/PlayoffType"},
                {"type": "null"},
            ],
        )
        self.assertEqual(
            properties["double_elim_round"]["$ref"],
            "#/components/schemas/Double_Elim_Round",
        )
        self.assertNotIn("playoff_type", playoff.get("required", []))
        self.assertNotIn("double_elim_round", playoff.get("required", []))
