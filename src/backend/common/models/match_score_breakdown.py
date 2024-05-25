from typing import Dict

from backend.common.consts.alliance_color import AllianceColor

# Fully typing this is a lot and depends on the year.
# We can come back to this
# Additionally, in 2015 there are more top level keys
# - coopertition (one of: Set, Stack, Unknown)
# - coopertition_points (int)
# We ignore these for now...
MatchScoreBreakdown = Dict[AllianceColor, Dict]
