from typing import Dict, List, NewType

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.insight_v2 import InsightV2
from backend.common.queries.dict_converters.converter_base import ConverterBase

InsightV2Dict = NewType("InsightV2Dict", Dict)


class InsightV2Converter(ConverterBase):
    SUBVERSIONS = {
        ApiMajorVersion.API_V3: 0,
    }

    @classmethod
    def _convert_list(
        cls, model_list: List[InsightV2], version: ApiMajorVersion
    ) -> List[InsightV2Dict]:
        CONVERTERS = {
            ApiMajorVersion.API_V3: cls._convert_list_v3,
        }
        return CONVERTERS[version](model_list)

    @classmethod
    def _convert_list_v3(cls, insights: List[InsightV2]) -> List[InsightV2Dict]:
        return [cls._convert_one_v3(i) for i in insights]

    @classmethod
    def _convert_one_v3(cls, insight: InsightV2) -> InsightV2Dict:
        return InsightV2Dict(
            {
                "name": insight.name,
                "display_name": insight.display_name,
                "year": insight.year,
                "category": insight.category,
                "district_abbreviation": insight.district_abbreviation,
                "data": insight.data_json,
            }
        )
