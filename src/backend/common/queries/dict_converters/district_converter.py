from typing import Dict, List

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.district import District
from backend.common.queries.dict_converters.converter_base import ConverterBase


class DistrictConverter(ConverterBase):
    # SUBVERSIONS = {  # Increment every time a change to the dict is made
    #     3: 2,
    # }
    # TODO use for cache clearing

    @classmethod
    def _convert(
        cls, districts: List[District], version: ApiMajorVersion
    ) -> List[Dict]:
        CONVERTERS = {
            3: cls.districtsConverter_v3,
        }
        return CONVERTERS[version](districts)

    @classmethod
    def districtsConverter_v3(cls, districts: List[District]) -> List[Dict]:
        return list(map(cls.districtConverter_v3, districts))

    @classmethod
    def districtConverter_v3(cls, district: District) -> Dict:
        return {
            "key": district.key.id(),
            "year": district.year,
            "abbreviation": district.abbreviation,
            "display_name": district.display_name,
        }
