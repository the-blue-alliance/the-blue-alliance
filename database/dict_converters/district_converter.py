from database.dict_converters.converter_base import ConverterBase


class DistrictConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 0,
    }

    @classmethod
    def convert(cls, districts, dict_version):
        DISTRICT_CONVERTERS = {
            3: cls.districtsConverter_v3,
        }
        return DISTRICT_CONVERTERS[dict_version](districts)

    @classmethod
    def districtsConverter_v3(cls, districts):
        districts_dict = {}
        for year, year_key in districts.items():
            year_key = year_key.split('_')[0]
            districts_dict[year] = year_key[4:]
        return districts_dict
