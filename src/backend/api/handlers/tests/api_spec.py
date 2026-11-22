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
def _spec(spec_name: str) -> Dict[str, Any]:
    with open(os.path.join(SWAGGER_DIR, spec_name)) as f:
        return json.load(f)


@lru_cache(maxsize=None)
def _registry(spec_name: str) -> Registry:
    spec = _spec(spec_name)
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
    return _errors(spec_name, pointer, body)


def component_schema_errors(
    name: str, body: Any, spec_name: str = "api_v3.json"
) -> List[str]:
    """
    Validates |body| against the spec's `#/components/schemas/<name>`, for
    checking one branch of a union directly.
    """
    return _errors(spec_name, f"/components/schemas/{_escape(name)}", body)


def _errors(spec_name: str, pointer: str, body: Any) -> List[str]:
    schema: Dict[str, Any] = {"$ref": f"urn:tba:{spec_name}#{pointer}"}
    validator = Draft202012Validator(schema, registry=_registry(spec_name))
    return sorted(
        {
            f"{error.json_path}: {error.message}"
            for error in _leaf_errors(validator.iter_errors(body))
        }
    )


def undeclared_fields(
    name: str, body: Any, spec_name: str = "api_v3.json"
) -> List[str]:
    """
    Returns the JSON path of every object key in |body| that the spec's
    `#/components/schemas/<name>` does not declare. JSON Schema allows
    undeclared keys unless a schema forbids them, so validation alone does not
    catch fields the spec omits. Follows `$ref`, `allOf`, `properties`, and
    `items`; does not descend into `oneOf`/`anyOf`.
    """
    spec = _spec(spec_name)

    def resolve(schema: Dict[str, Any]) -> Dict[str, Any]:
        while "$ref" in schema:
            schema = spec["components"]["schemas"][schema["$ref"].split("/")[-1]]
        return schema

    def properties(schema: Dict[str, Any]) -> Dict[str, Any]:
        schema = resolve(schema)
        props: Dict[str, Any] = {}
        for sub in schema.get("allOf", []):
            props.update(properties(sub))
        props.update(schema.get("properties", {}))
        return props

    def walk(path: str, value: Any, schema: Dict[str, Any]) -> List[str]:
        schema = resolve(schema)
        found: List[str] = []
        if isinstance(value, dict):
            props = properties(schema)
            for key, child in value.items():
                if key in props:
                    found.extend(walk(f"{path}.{key}", child, props[key]))
                else:
                    found.append(f"{path}.{key}")
        elif isinstance(value, list) and "items" in schema:
            for i, child in enumerate(value):
                found.extend(walk(f"{path}[{i}]", child, schema["items"]))
        return found

    return sorted(walk("$", body, {"$ref": f"#/components/schemas/{name}"}))
