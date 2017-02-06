import functools

from swagger.swagger_parameters import SwaggerParameter
from swagger.swagger_responses import SwaggerResponse


class ApiV3Endpoint(object):
    """
    A decorator for apiv3 controller render methods
    These will be used to auto-generate a schema
    """

    all_endpoints = []

    def __init__(self, path, description, parameters, response):
        """
        :param path: Swagger-Compliant URL, can reference parameters
        :param description: Description of this endpoint
        :param parameters: List of things extending SwaggerParameter
        :param response: Thing extending SwaggerResponse that is returned on success
        """

        # Validate that parameters and response items
        if not isinstance(parameters, list):
            parameters = [parameters]
        for param in parameters:
            if not isinstance(param, SwaggerParameter):
                raise ValueError("{} is not an instance of SwaggerParameter".format(param))
        if not isinstance(response, SwaggerResponse):
            raise ValueError("{} is not an instance of SwaggerResponse".format(response))

        self.path = path
        self.description = description
        self.parameters = parameters
        self.response = response

    def __call__(self, fn):

        @functools.wraps(fn)
        def decorated(*args, **kwargs):
            fn(*args, **kwargs)

        # Store our properties as function attributes, nesting if needed
        if not hasattr(decorated, 'swagger_props') or not isinstance(decorated.swagger_props, list):
            decorated.swagger_props = []

        decorated.swagger_props.append((self.path, {
            'description': self.description,
            'parameters': [{"$ref": "parameters.json#/{}".format(param.name)} for param in self.parameters],
            'responses': {
                "200": {
                    "schema": {
                        "$ref": "{}.json".format(self.response.name)
                    },

                },
            }
        }))
        return decorated
