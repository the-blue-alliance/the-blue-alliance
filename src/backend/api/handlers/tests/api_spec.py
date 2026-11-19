import json
import os
from functools import lru_cache
from typing import Any, Dict, Iterable, List

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry
from referencing.jsonschema import DRAFT202012

SWAGGER_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "web", "static", "swagger"
)


@lru_cache(maxsize=None)
def _registry(spec_name: str) -> Registry:
    with open(os.path.join(SWAGGER_DIR, spec_name)) as f:
        spec = json.load(f)
    resource = DRAFT202012.create_resource(spec)
    return Registry().with_resource(f"urn:tba:{spec_name}", resource)


def _leaf_errors(errors: Iterable[ValidationError]) -> List[ValidationError]:
    leaves = []
    for error in errors:
        leaves.extend(_leaf_errors(error.context) if error.context else [error])
    return leaves


def _escape(segment: str) -> str:
    return segment.replace("~", "~0").replace("/", "~1")


def response_schema_errors(
    path: str,
    body: Any,
    spec_name: str = "api_v3.json",
    method: str = "get",
    status: str = "200",
) -> List[str]:
    """
    Validates |body| against the response schema the OpenAPI spec |spec_name|
    declares for |method| |path| (a spec path template, such as
    "/event/{event_key}/insights") and returns one message per violation.
    `$ref`s resolve against the whole spec document.
    """
    pointer = "/".join(
        [
            "",
            "paths",
            _escape(path),
            method,
            "responses",
            status,
            "content",
            "application~1json",
            "schema",
        ]
    )
    schema: Dict[str, Any] = {"$ref": f"urn:tba:{spec_name}#{pointer}"}
    validator = Draft202012Validator(schema, registry=_registry(spec_name))
    return sorted(
        {
            f"{error.json_path}: {error.message}"
            for error in _leaf_errors(validator.iter_errors(body))
        }
    )
