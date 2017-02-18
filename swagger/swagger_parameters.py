
class SwaggerParameter(object):
    """
    Represents a path/header parameter for a request
    """

    def __init__(self, name, location, description, required, type):
        self.name = name
        self.location = location
        self.description = description
        self.required = required
        self.type = type

    def render(self):
        return {
            'name': self.name,
            'in': self.location,
            'description': self.description,
            'required': self.required,
            'type': self.type,
        }


IfModifiedParameter = SwaggerParameter(
    name="If-Modified-Since",
    location='header',
    description='Value of the Last-Modified header in the most recent client side response',
    required=False,
    type='string',
)

TeamKeyParameter = SwaggerParameter(
    name='team_key',
    location='path',
    description='TBA Team Key, eg `frc254`',
    required=True,
    type='string',
)
