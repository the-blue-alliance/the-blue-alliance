import json

from backend.common.models.regional_pool_advancement import (
    ChampionshipStatus,
    TeamRegionalPoolAdvancement,
)
from backend.tasks_io.datafeeds.parsers.ra.regional_advancement_parser import (
    RegionalAdvancementParser,
)


def test_parse_advancement(test_data_importer) -> None:
    path = test_data_importer._get_path(__file__, "data/2025ra.json")
    with open(path, "r") as f:
        data = json.load(f)

    result = RegionalAdvancementParser().parse(data)
    assert len(result.advancement) == 223
    assert result.advancement["frc694"] == TeamRegionalPoolAdvancement(
        cmp=True,
        cmp_status=ChampionshipStatus.EVENT_QUALIFIED,
        qualifying_award_name="Regional Winner",
        qualifying_event="2025nysu",
    )

    assert result.advancement["frc5736"] == TeamRegionalPoolAdvancement(
        cmp=True,
        cmp_status=ChampionshipStatus.POOL_QUALIFIED,
        qualifying_pool_week=2,
    )

    assert result.advancement["frc9432"] == TeamRegionalPoolAdvancement(
        cmp=True,
        cmp_status=ChampionshipStatus.PRE_QUALIFIED,
    )

    assert result.advancement["frc1339"] == TeamRegionalPoolAdvancement(
        cmp=False,
        cmp_status=ChampionshipStatus.DECLINED,
    )


def test_parse_advancement_skips_not_invited(test_data_importer) -> None:
    path = test_data_importer._get_path(__file__, "data/2025ra.json")
    with open(path, "r") as f:
        data = json.load(f)

    result = RegionalAdvancementParser().parse(data)
    assert not any(
        a["cmp_status"] == ChampionshipStatus.NOT_INVITED
        for _, a in result.advancement.items()
    )


def test_parse_adjustments(test_data_importer) -> None:
    path = test_data_importer._get_path(__file__, "data/2025ra.json")
    with open(path, "r") as f:
        data = json.load(f)

    result = RegionalAdvancementParser().parse(data)
    assert result.adjustments == {
        "frc10446": 1,
        "frc1056": 2,
        "frc1421": 1,
        "frc159": 1,
        "frc1912": 1,
        "frc2036": 1,
        "frc2221": 1,
        "frc3284": 1,
        "frc4329": 1,
        "frc4500": 1,
        "frc6017": 2,
        "frc7472": 1,
        "frc8044": 1,
        "frc9068": 1,
        "frc9734": 1,
    }
