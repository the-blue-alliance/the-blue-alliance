import pytest

from backend.common.consts.renamed_districts import RenamedDistricts
from backend.common.models.district import District


@pytest.mark.parametrize(
    "code, year, expected",
    [
        ("fit", 2020, "tx"),
        ("tx", 2023, "fit"),
        ("fit", 2026, "tx"),
        ("fit", 2027, "tx"),
        ("mar", 2019, "fma"),
        ("fma", 2014, "mar"),
        ("chs", 2026, "fch"),
        ("fit", 2017, "tx"),
        ("fim", 2026, "fim"),
    ],
)
def test_get_code_for_year(code: str, year: int, expected: str) -> None:
    assert RenamedDistricts.get_code_for_year(code, year) == expected


@pytest.mark.parametrize(
    "district_key, expected",
    [
        ("2026fit", "2026tx"),
        ("2025tx", "2025fit"),
        ("2026tx", "2026tx"),
        ("2026fim", "2026fim"),
        ("bogus", "bogus"),
    ],
)
def test_get_key_for_year(district_key: str, expected: str) -> None:
    assert RenamedDistricts.get_key_for_year(district_key) == expected


@pytest.mark.parametrize("code", ["tx", "fit"])
def test_texas_canonical_code_is_fit(code: str) -> None:
    assert RenamedDistricts.get_canonical_code(code) == "fit"


def test_equivalent_codes_start_with_the_given_code() -> None:
    assert RenamedDistricts.get_equivalent_codes("tx") == ["tx", "fit"]


def test_equivalent_codes_of_unrenamed_district() -> None:
    assert RenamedDistricts.get_equivalent_codes("fim") == ["fim"]


def test_canonical_codes_exclude_old_codes() -> None:
    assert {"tx", "mar", "nc", "in", "chs"}.isdisjoint(
        RenamedDistricts.get_canonical_codes()
    )


def test_district_exists_under_other_code(ndb_stub) -> None:
    District(id="2026tx", year=2026, abbreviation="tx").put()

    assert RenamedDistricts.district_exists_async("2026fit").get_result()


def test_stray_district_under_wrong_code_does_not_count(ndb_stub) -> None:
    District(id="2026fit", year=2026, abbreviation="fit").put()

    assert not RenamedDistricts.district_exists_async("2026fit").get_result()


def test_district_exists_requires_a_row(ndb_stub) -> None:
    assert not RenamedDistricts.district_exists_async("2026tx").get_result()
