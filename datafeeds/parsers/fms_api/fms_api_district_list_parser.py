from models.district import District


class FMSAPIDistrictListParser(object):

    def __init__(self, season):
        self.season = int(season)

    def parse(self, response):
        districts = []

        for district in response['districts']:
            district_code = district['code'].lower()
            district_key = District.renderKeyName(self.season, district_code)
            districts.append(District(
                id=district_key,
                abbreviation=district_code,
                year=self.season,
                display_name=district['name'],
            ))

        return districts
