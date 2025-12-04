import json
from typing import NewType

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.insight import Insight
from backend.common.queries.dict_converters.converter_base import ConverterBase

InsightDict = NewType("InsightDict", dict)


class InsightConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        ApiMajorVersion.API_V3: 0,
    }

    @classmethod
    def _convert_list(
        cls, model_list: list[Insight], version: ApiMajorVersion
    ) -> list[InsightDict]:
        INSIGHT_CONVERTERS = {
            ApiMajorVersion.API_V3: cls.insightsConverter_v3,
        }
        return INSIGHT_CONVERTERS[version](model_list)

    @classmethod
    def insightsConverter_v3(cls, insights: list[Insight]) -> list[InsightDict]:
        return list(map(cls.insightConverter_v3, insights))

    @classmethod
    def insightConverter_v3(cls, insight: Insight) -> InsightDict:
        return InsightDict(
            {
                "name": insight.name,
                "data": json.loads(insight.data_json),
                "year": insight.year,
            }
        )
