from typing import Dict, List

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.district import District
from backend.common.queries.dict_converters.converter_base import ConverterBase


class DistrictConverter(ConverterBase):
    # SUBVERSIONS = {  # Increment every time a change to the dict is made
    #     3: 2,
    # }
    # TODO use for cache clearing

    def _convert_list(
        self, model_list: List[District], version: ApiMajorVersion
    ) -> List[Dict]:
        CONVERTERS = {
            3: self.districtsConverter_v3,
        }
        return CONVERTERS[version](model_list)

    def districtsConverter_v3(self, districts: List[District]) -> List[Dict]:
        return list(map(self.districtConverter_v3, districts))

    def districtConverter_v3(self, district: District) -> Dict:
        return {
            "key": district.key.id(),
            "year": district.year,
            "abbreviation": district.abbreviation,
            "display_name": district.display_name,
        }

    @staticmethod
    def dictToModel_v3(data: Dict) -> District:
        district = District(id=data["key"])
        district.year = data["year"]
        district.abbreviation = data["abbreviation"]
        district.display_name = data["display_name"]
        return district
