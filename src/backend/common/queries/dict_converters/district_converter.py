from typing import Dict, List, NewType

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.district import District
from backend.common.queries.dict_converters.converter_base import ConverterBase

DistrictDict = NewType("DistrictDict", Dict)


class DistrictConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        ApiMajorVersion.API_V3: 2,
    }

    @classmethod
    def _convert_list(
        cls, model_list: List[District], version: ApiMajorVersion
    ) -> List[DistrictDict]:
        CONVERTERS = {
            3: cls.districtsConverter_v3,
        }
        return CONVERTERS[version](model_list)

    @classmethod
    def districtsConverter_v3(cls, districts: List[District]) -> List[DistrictDict]:
        return list(map(cls.districtConverter_v3, districts))

    @classmethod
    def districtConverter_v3(cls, district: District) -> DistrictDict:
        return DistrictDict(
            {
                "key": district.key.id(),
                "year": district.year,
                "abbreviation": district.abbreviation,
                "display_name": district.display_name,
            }
        )

    @staticmethod
    def dictToModel_v3(data: Dict) -> District:
        district = District(id=data["key"])
        district.year = data["year"]
        district.abbreviation = data["abbreviation"]
        district.display_name = data["display_name"]
        return district
