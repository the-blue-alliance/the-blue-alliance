from backend.common.models.district import District
from backend.common.models.district_advancement import AdvancementCounts
from backend.common.queries.dict_converters.district_converter import DistrictConverter


def test_districtConverter_v3_basic(ndb_context) -> None:
    district = District(
        id="2025ne",
        year=2025,
        abbreviation="ne",
        display_name="New England",
    )

    converted = DistrictConverter.districtConverter_v3(district)

    assert converted["key"] == "2025ne"
    assert converted["year"] == 2025
    assert converted["abbreviation"] == "ne"
    assert converted["display_name"] == "New England"


def test_districtConverter_v3_with_known_advancement_counts(ndb_context) -> None:
    district = District(
        id="2025ne",
        year=2025,
        abbreviation="ne",
        display_name="New England",
    )

    converted = DistrictConverter.districtConverter_v3(district)

    assert converted["official_advancement_counts"] == AdvancementCounts(
        dcmp=96, cmp=31
    )


def test_districtConverter_v3_unknown_year_returns_zero_counts(ndb_context) -> None:
    district = District(
        id="2000ne",
        year=2000,
        abbreviation="ne",
        display_name="New England",
    )

    converted = DistrictConverter.districtConverter_v3(district)

    assert converted["official_advancement_counts"] == AdvancementCounts(dcmp=0, cmp=0)


def test_districtConverter_v3_unknown_abbreviation_returns_zero_counts(
    ndb_context,
) -> None:
    district = District(
        id="2025xyz",
        year=2025,
        abbreviation="xyz",
        display_name="Unknown District",
    )

    converted = DistrictConverter.districtConverter_v3(district)

    assert converted["official_advancement_counts"] == AdvancementCounts(dcmp=0, cmp=0)


def test_districtConverter_v3_advancement_works_for_old_and_new_district_names(
    ndb_context,
) -> None:
    old_district = District(
        id="2012mar",
        year=2012,
        abbreviation="mar",
        display_name="Mid Atlantic",
    )
    new_district = District(
        id="2013fma",
        year=2013,
        abbreviation="fma",
        display_name="Mid Atlantic",
    )

    converted_old = DistrictConverter.districtConverter_v3(old_district)
    converted_new = DistrictConverter.districtConverter_v3(new_district)

    assert converted_old["official_advancement_counts"] == AdvancementCounts(
        dcmp=53, cmp=12
    )
    assert converted_new["official_advancement_counts"] == AdvancementCounts(
        dcmp=49, cmp=14
    )
