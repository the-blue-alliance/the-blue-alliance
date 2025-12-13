from datetime import datetime
from typing import Optional

from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.keys import Year
from backend.common.models.regional_champs_pool import RegionalChampsPool
from backend.web.profiled_render import render_template


def regional_champs_pool_list(year: Optional[Year]) -> str:
    if not year:
        year = datetime.now().year

    pool_model = RegionalChampsPool.get_by_id(RegionalChampsPool.render_key_name(year))
    template_values = {
        "valid_years": reversed(SeasonHelper.get_valid_regional_pool_years()),
        "selected_year": year,
        "pool_model": pool_model,
    }
    return render_template("admin/regional_champs_pool_list.html", template_values)
