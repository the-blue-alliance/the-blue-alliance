import os
from typing import List, Optional

from backend.common.consts.alliance_color import AllianceColor
from backend.common.game_specific.base import TCriteria

# Sentinel: dirname(_HELPERS_TESTS) == .../helpers/tests/ so that
# test_data_importer._get_path() resolves files from that directory.
HELPERS_TESTS = os.path.join(os.path.dirname(__file__), "../../../helpers/tests/x")


def tiebreak_winner(criteria: List[Optional[TCriteria]]) -> str:
    """Walk criteria list, return winning AllianceColor or empty string."""
    for c in criteria:
        if c is None:
            break
        if c[0] > c[1]:
            return AllianceColor.RED
        elif c[1] > c[0]:
            return AllianceColor.BLUE
    return ""
