from typing import Dict, List


from backend.common.models.keys import DistrictAbbreviation, DistrictKey

CODE_MAP: Dict[DistrictAbbreviation, DistrictAbbreviation] = {
    # Old to new
    "mar": "fma",
    "nc": "fnc",
    "in": "fin",
}

# Add new to old
for old, new in CODE_MAP.items():
    CODE_MAP[new] = old


class RenamedDistricts(object):
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
