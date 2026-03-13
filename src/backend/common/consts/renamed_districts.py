from typing import Any, Dict, Generator, List, Set

from google.appengine.ext import ndb

from backend.common.models.keys import DistrictAbbreviation, DistrictKey

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

OLD_TO_NEW_CODE_MAP: Dict[DistrictAbbreviation, DistrictAbbreviation] = {
    # Old to new
    "mar": "fma",
    "nc": "fnc",
    "in": "fin",
    "tx": "fit",
    "chs": "fch",
}

NEW_TO_OLD_CODE_MAP: Dict[DistrictAbbreviation, DistrictAbbreviation] = {
    v: k for k, v in OLD_TO_NEW_CODE_MAP.items()
}

CODE_MAP: Dict[DistrictAbbreviation, DistrictAbbreviation] = {
    **OLD_TO_NEW_CODE_MAP,
    **NEW_TO_OLD_CODE_MAP,
}


class RenamedDistricts:
    @staticmethod
    def get_equivalent_codes(code: DistrictAbbreviation) -> List[DistrictAbbreviation]:
        # Returns a list of equivalent district codes
        codes = [code]
        if code in CODE_MAP:
            codes.append(CODE_MAP[code])
        return codes

    @classmethod
    def get_equivalent_keys(cls, district_key: DistrictKey) -> List[DistrictKey]:
        year = district_key[:4]
        code = district_key[4:]
        return [
            "{}{}".format(year, equiv_code)
            for equiv_code in cls.get_equivalent_codes(code)
        ]

    @classmethod
    def get_latest_codes(cls) -> List[DistrictAbbreviation]:
        seen = set()
        for abbr in ALL_KNOWN_DISTRICT_ABBREVIATIONS:
            seen.add(OLD_TO_NEW_CODE_MAP.get(abbr, abbr))

        return list(seen)

    @classmethod
    def get_latest_code(cls, code: DistrictAbbreviation) -> DistrictAbbreviation:
        return OLD_TO_NEW_CODE_MAP.get(code, code)

    @classmethod
    @ndb.tasklet
    def district_exists_async(
        cls, district_key: DistrictKey
    ) -> Generator[Any, Any, bool]:
        keys = [ndb.Key("District", k) for k in cls.get_equivalent_keys(district_key)]
        districts = yield ndb.get_multi_async(keys)
        districts = list(filter(lambda d: d is not None, districts))
        return len(districts) > 0
