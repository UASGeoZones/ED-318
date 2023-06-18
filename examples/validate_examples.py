# Validation script to ensure that the examples validate against the defined schema.
# See Dockerfile to run this script with Docker rather than setting up an environment with requirements.txt.

import os.path
from dataclasses import dataclass
import json
from pathlib import Path
from typing import List, Optional

import bc_jsonpath_ng
import jsonschema.validators


@dataclass
class ValidationError(object):
    """Error encountered while validating an instance against a schema."""

    message: str
    """Validation error message."""

    json_path: str
    """Location of the data causing the validation error."""


def _collect_errors(e: jsonschema.ValidationError) -> List[ValidationError]:
    if e.context:
        result = []
        for child in e.context:
            result.extend(_collect_errors(child))
        return result
    else:
        return [ValidationError(message=e.message, json_path=e.json_path)]


def validate(schema_path: str, object_path: str, instance: dict, instance_path: Optional[str] = None) -> List[ValidationError]:
    with open(schema_path, "r") as f:
        schema_content = json.load(f)

    schema_matches = bc_jsonpath_ng.parse(object_path).find(schema_content)
    if len(schema_matches) != 1:
        raise ValueError(
            f"Found {len(schema_matches)} matches to JSON path '{object_path}' within OpenAPI definition when expecting exactly 1 match"
        )
    schema = schema_matches[0].value

    if instance_path is not None:
        instance_matches = bc_jsonpath_ng.parse(instance_path).find(instance)
        if len(instance_matches) != 1:
            raise ValueError(
                f"Found {len(instance_matches)} matches to JSON path '{instance_path}' within value to validate when expecting exactly 1 match"
            )
        value = instance_matches[0].value
    else:
        value = instance

    validator_class = jsonschema.validators.validator_for(schema)
    validator_class.check_schema(schema)

    ref_resolver = jsonschema.RefResolver(f"{Path(schema_path).as_uri()}", schema_content)
    validator = validator_class(schema, resolver=ref_resolver)
    result = []
    for e in validator.iter_errors(value):
        result.extend(_collect_errors(e))
    return result


def main():
    root = os.path.realpath(os.path.join(os.path.split(__file__)[0], ".."))

    # (Example file minus extension, JSONPath in example object, schema file minus extension, JSONPath in schema)
    to_validate = (
        ("Example_GeoZone_2_Layers",         "$", "Schema_GeoZones",          "$"),
        ("PartialExample_featureGeoJSON",    "$", "Schema_GeoZones",          "$"),
        ("PartialExample_GeoZoneProperties", "$", "Schema_GeoZoneProperties", "$"),
        ("PartialExample_TimePeriod",        "$", "Schema_GeoZoneTimePeriod", "$"),
        ("PartialExample_ZoneAuthority",     "$", "Schema_GeoZoneAuthority",  "$"),
    )

    for example, example_jsonpath, schema_file, schema_jsonpath in to_validate:
        schema_path = os.path.join(root, "schema", schema_file + ".json")
        instance_path = os.path.join(root, "examples", example + ".json")
        with open(instance_path, "r") as f:
            instance_content = json.load(f)

        errors = validate(schema_path, schema_jsonpath, instance_content, example_jsonpath)
        if errors:
            print(f"{example}: {len(errors)} errors found")
            for e in errors:
                print(f"  * {e.json_path}: {e.message}")
                print()
        else:
            print(f"{example}: No errors found.")


if __name__ == "__main__":
    main()
