from collections import defaultdict
from typing import DefaultDict, List, Optional

from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.insight import Insight
from backend.common.models.keys import Year
from backend.web.profiled_render import render_template


def insights_list(year: Optional[Year]) -> str:
    if year is None:
        year = SeasonHelper.get_current_season()

    all_insights: List[Insight] = Insight.query(Insight.year == year).fetch(10000)

    global_insights = sorted(
        [i for i in all_insights if not i.district_abbreviation],
        key=lambda i: i.name,
    )

    by_district: DefaultDict[str, List[Insight]] = defaultdict(list)
    for insight in all_insights:
        if insight.district_abbreviation:
            by_district[insight.district_abbreviation].append(insight)
    # Sort each district's list by name
    district_insights = {
        abbrev: sorted(insights, key=lambda i: i.name)
        for abbrev, insights in sorted(by_district.items())
    }

    template_values = {
        "year": year,
        "valid_years": list(reversed(SeasonHelper.get_valid_years())),
        "global_insights": global_insights,
        "district_insights": district_insights,
    }

    return render_template("admin/insights.html", template_values)
