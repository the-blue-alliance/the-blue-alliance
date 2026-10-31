from typing import Any, Dict, Generator, List, Set

from google.appengine.ext import ndb

from backend.common.models.keys import DistrictAbbreviation, DistrictKey, Year

ALL_KNOWN_DISTRICT_ABBREVIATIONS: Set[DistrictAbbreviation] = {
    "chs",
    "fch",
    "fim",
    "fit",
    "tx",
    "in",
    "fin",
    "isr",
    "mar",
    "fma",
    "nc",
    "fnc",
    "fsc",
    "ne",
    "ont",
    "pnw",
    "pch",
    "ca",
    "win",
}

DISTRICT_CODE_HISTORY: Dict[DistrictAbbreviation, Dict[Year, DistrictAbbreviation]] = {
    "fma": {2012: "mar", 2019: "fma"},
    "fnc": {2016: "nc", 2019: "fnc"},
    "fin": {2015: "in", 2021: "fin"},
    "fit": {2019: "tx", 2021: "fit", 2026: "tx"},
    "fch": {2016: "chs", 2026: "fch"},
}

CANONICAL_CODES: Dict[DistrictAbbreviation, DistrictAbbreviation] = {
    code: canonical
    for canonical, codes_by_year in DISTRICT_CODE_HISTORY.items()
    for code in [canonical, *codes_by_year.values()]
}


class RenamedDistricts:
    @staticmethod
    def get_canonical_code(code: DistrictAbbreviation) -> DistrictAbbreviation:
        return CANONICAL_CODES.get(code, code)

    @classmethod
    def get_canonical_codes(cls) -> List[DistrictAbbreviation]:
        return list(
            {cls.get_canonical_code(c) for c in ALL_KNOWN_DISTRICT_ABBREVIATIONS}
        )

    @classmethod
    def get_equivalent_codes(
        cls, code: DistrictAbbreviation
    ) -> List[DistrictAbbreviation]:
        canonical = cls.get_canonical_code(code)
        codes_by_year = DISTRICT_CODE_HISTORY.get(canonical, {})
        others = {canonical, *codes_by_year.values()} - {code}
        return [code, *sorted(others)]

    @classmethod
    def get_equivalent_keys(cls, district_key: DistrictKey) -> List[DistrictKey]:
        year = district_key[:4]
        code = district_key[4:]
        return [
            "{}{}".format(year, equiv_code)
            for equiv_code in cls.get_equivalent_codes(code)
        ]

    @classmethod
    def get_code_for_year(
        cls, code: DistrictAbbreviation, year: Year
    ) -> DistrictAbbreviation:
        codes_by_year = DISTRICT_CODE_HISTORY.get(cls.get_canonical_code(code))
        if not codes_by_year:
            return code
        start_year = max(
            (y for y in codes_by_year if y <= year), default=min(codes_by_year)
        )
        return codes_by_year[start_year]

    @classmethod
    def get_key_for_year(cls, district_key: DistrictKey) -> DistrictKey:
        year = district_key[:4]
        if not year.isdigit():
            return district_key
        return f"{year}{cls.get_code_for_year(district_key[4:], int(year))}"

    @classmethod
    @ndb.tasklet
    def district_exists_async(
        cls, district_key: DistrictKey
    ) -> Generator[Any, Any, bool]:
        district = yield ndb.Key(
            "District", cls.get_key_for_year(district_key)
        ).get_async()
        return district is not None
