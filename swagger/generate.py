"""
Script to generate swagger files from our code
"""
import json
import sys

# HACKY (but necessary...)
sys.path.insert(1, 'lib')

from swagger import swagger_parameters
from swagger import swagger_responses
import apiv3_main

base_json = {
    "swagger": "2.0",
    "info": {
        "description": "The Blue Alliance API v3.",
        "version": "3.0.0 beta",
        "title": "TBA API v3"
    },
    "host": "www.thebluealliance.com",
    "basePath": "/api/v3",
    "tags": [
        {
            "name": "TBA",
            "description": "Calls that expose TBA internals or status."
        },
        {
            "name": "list",
            "description": "Calls that return a list of records."
        },
        {
            "name": "team",
            "description": "Calls that return team or team-specific information."
        },
        {
            "name": "event",
            "description": "Calls that return event, or event-specific information."
        },
        {
            "name": "match",
            "description": "Calls that return match, or match-specific information."
        },
        {
            "name": "district",
            "description": "Calls that return district, or district-related information."
        }
    ],
    "schemes": [
        "https"
    ],
    "produces": [
        "application/json"
    ],
    "securityDefinitions": {
        "apiKey": {
            "description": "Your TBA API Key can be obtained from your Account Page on the TBA website.",
            "type": "apiKey",
            "name": "X-TBA-API-Key",
            "in": "header"
        }
    },
    "paths": {},
    "parameters": {},
    "definitions": {},
}

if __name__ == '__main__':
    # Show all the URL routes
    routes = apiv3_main.app.router.match_routes
    handlers = set()

    for route in routes:
        handlers.add(route.handler)
    print "Found {} APIv3 routes and {} handlers".format(len(routes), len(handlers))

    # Generate paths
    for handler in handlers:
        if hasattr(handler, '_render') and hasattr(handler._render, 'swagger_props'):
            print "Processing {}.{}".format(handler.__module__, handler.__name__)
            endpoints = handler._render.swagger_props
            for path, endpoint in endpoints:
                # Add in some common things to build the entire object
                endpoint['responses']['200']['headers'] = {
                    "Last-Modified": {
                        "type": "string",
                        "description": "Indicates the date and time the data returned was last updated. Used by clients in the `If-Modified-Since` request header."
                    },
                    "Cache-Control": {
                        "type": "string",
                        "description": "The `Cache-Control` header, in particular the `max-age` value, contains the number of seconds the result should be considered valid for. During this time subsequent calls should return from the local cache directly."
                    }
                }
                endpoint['parameters'].append({'$ref': '#/parameters/If-Modified-Since'})
                endpoint['responses']['200']['description'] = 'Successful Response'
                #endpoint['responses']['304'] = {
                #    '$ref': '#/responses/NotModified'
                #}
                base_json['paths'].update({path: {'get': endpoint}})

    # Generate Parameters
    parameters = filter(lambda x: not x.startswith("__") and x != "SwaggerParameter", dir(swagger_parameters))
    params_json = {}
    for param in parameters:
        var = getattr(swagger_parameters, param)
        params_json[var.name] = var.render()
    base_json['parameters'] = params_json

    # Generate Responses
    responses = filter(lambda x: not x.startswith("__") and x != "SwaggerResponse", dir(swagger_responses))
    responses_json = {}
    for resp in responses:
        var = getattr(swagger_responses, resp)
        responses_json[var.name] = var.render()
    base_json['definitions'] = responses_json

    with open("static/swagger.json", "w") as text_file:
        text_file.write(json.dumps(base_json, indent=2))
