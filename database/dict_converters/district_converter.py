from consts.district_type import DistrictType
from database.dict_converters.converter_base import ConverterBase


class DistrictConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 2,
    }

    @classmethod
    def _convert(cls, districts, dict_version):
        CONVERTERS = {
            3: cls.districtsConverter_v3,
        }
        return CONVERTERS[dict_version](districts)

    @classmethod
    def districtsConverter_v3(cls, districts):
        districts = map(cls.districtConverter_v3, districts)
        return districts

    @classmethod
    def districtConverter_v3(cls, district):
        district_dict = {
            'key': district.key.id(),
            'year': district.year,
            'abbreviation': district.abbreviation,
            'display_name': district.display_name,
        }

        return district_dict
