
class SwaggerResponse(object):
    """
    Represents an API response
    """

    def __init__(self, name, object):
        self.name = name
        self.object = object

    def render(self):
        return self.object


SimpleTeamResponse = SwaggerResponse(
    name='TeamSimple',
    object={
        'type': 'object',
        'required': [
            'key',
            'name',
            'team_number',
        ],
        'properties': {
            "key": {
                "type": "string",
                "description": "TBA team key with the format frcyyyy"
            },
            "team_number": {
                "type": "integer",
                "description": "Official team number issued by FIRST"
            },
            "nickname": {
                "type": "string",
                "description": "Team nickname provided by FIRST"
            },
            "name": {
                "type": "string",
                "description": "Official long name registered with FIRST"
            },
            "city": {
                "type": "string",
                "description": "City of team derived from parsing the address registered with FIRST"
            },
            "state_prov": {
                "type": "string",
                "description": "State of team derived from parsing the address registered with FIRST"
            },
            "country": {
                "type": "string",
                "description": "Country of team derived from parsing the address registered with FIRST"
            }
        }
    }
)

TeamResponse = SwaggerResponse(
    name='Team',
    object={
        "type": "object",
        "allOf": [
            {
                "$ref": "#/definitions/TeamSimple"
            }
        ],
        "required": [
            "rookie_year"
        ],
        "properties": {
            "address": {
                "type": "string",
                "description": "Address for the team"
            },
            "postal_code": {
                "type": "string",
                "description": "Postal code from the team address"
            },
            "gmaps_place_id": {
                "type": "string",
                "description": "Google Maps Place ID for the team address"
            },
            "gmaps_url": {
                "type": "string",
                "format": "url",
                "description": "Link to address location on Google Maps"
            },
            "lat": {
                "type": "number",
                "format": "double",
                "description": "Latitude for the team address"
            },
            "lng": {
                "type": "number",
                "format": "double",
                "description": "Longitude for the team address"
            },
            "location_name": {
                "type": "string",
                "description": "Name of the location at the address for the team, eg. Blue Alliance High School"
            },
            "website": {
                "type": "string",
                "format": "url",
                "description": "Official website associated with the team"
            },
            "rookie_year": {
                "type": "integer",
                "description": "First year the team officially competed"
            },
            "motto": {
                "type": "string",
                "description": "Team's motto as provided by FIRST"
            },
            "home_championship": {
                "type": "object",
                "description": "Location of the team's home championship each year as a key-value pair. The year is the key, and the city is the value."
            }
        }
    }
)
