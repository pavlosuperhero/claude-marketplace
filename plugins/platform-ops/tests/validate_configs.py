#!/usr/bin/env python3
# /// script
# dependencies = [
#     "pyyaml",
#     "jsonschema>=4.22,<5",
#     "referencing>=0.28,<1",
# ]
# ///
"""
Specification & Config Validator
Validates application YAML configurations against JSON schemas.
Uses PEP 723 metadata for automated dependency management via 'uv run'.

CLI Usage:
  uv run tests/validate_configs.py --config /path/to/config.yaml --schema /path/to/schema.json
  # Or multiple files:
  uv run tests/validate_configs.py config1.yaml config2.yaml
"""

import argparse
import json
import os
from pathlib import Path
import sys

import yaml
from jsonschema.exceptions import SchemaError
from jsonschema.validators import validator_for
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

# The validator is a standalone script invoked by both uv and the Claude Code hook.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from platform_ops_paths import PLUGIN_ROOT, add_specs_argument, find_specs_dir


SCHEMA_DIR = PLUGIN_ROOT / "schemas"
SCHEMA_FILES = {
    "app": "app-config.schema.json",
    "environment": "environment.schema.json",
    "service": "service-spec.schema.json",
}


def load_validator(schema_path):
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(schema, (dict, bool)):
        raise ValueError("A JSON Schema must be an object or a boolean.")
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)

    # Resolve the service schema's app contract from the installed plugin.
    app_schema = json.loads((SCHEMA_DIR / SCHEMA_FILES["app"]).read_text(encoding="utf-8"))
    registry = Registry().with_resource(app_schema["$id"], Resource.from_contents(app_schema))
    return validator_class(schema, registry=registry)


def validate_file(path, validator):
    try:
        with path.open(encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
        errors = list(validator.iter_errors(config))
    except (OSError, UnicodeError, yaml.YAMLError, Unresolvable) as error:
        print(f"[✗] ERROR: {path}: {error}")
        return False

    relative_path = os.path.relpath(path)
    if not errors:
        print(f"[✓] PASSED: {relative_path}")
        return True

    print(f"[✗] FAILED: {relative_path}")
    for error in errors:
        location = "config" + error.json_path[1:]
        print(f"    - {location}: {error.message}")
    return False


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate application YAML deployment configurations against JSON schema."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="One or more YAML configuration files to validate."
    )
    parser.add_argument(
        "-c", "--config",
        dest="single_config",
        default=None,
        help="Path to a single config YAML file."
    )
    parser.add_argument(
        "-s", "--schema",
        dest="schema_path",
        default=None,
        help="Path to the JSON schema (or env APP_SCHEMA_PATH for app configs)."
    )
    add_specs_argument(parser)
    parser.add_argument(
        "-t", "--schema-type",
        dest="schema_type",
        choices=["app", "environment", "service"],
        default="app",
        help="Schema type to validate against: 'app' (default), 'environment', or 'service'."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    target_files = [*args.files]
    if args.single_config:
        target_files.append(args.single_config)
    if not target_files:
        print("Usage: uv run tests/validate_configs.py <path-to-config.yaml> [--schema <schema.json>]")
        return 1

    configured_schema = args.schema_path
    if not configured_schema and args.schema_type == "app":
        configured_schema = os.environ.get("APP_SCHEMA_PATH")
    schema_path = Path(configured_schema).expanduser() if configured_schema else SCHEMA_DIR / SCHEMA_FILES[args.schema_type]
    try:
        validator = load_validator(schema_path)
    except (OSError, UnicodeError, ValueError, SchemaError) as error:
        print(f"Error loading schema {schema_path}: {error}", file=sys.stderr)
        return 1

    print("=" * 60)
    print("SPEC-DRIVEN DEVELOPMENT: CONFIG VALIDATOR")
    print(f"Schema: {os.path.relpath(schema_path)}")

    specs_dir = find_specs_dir(args.specs_dir)
    if specs_dir and specs_dir.is_dir():
        doc_count = sum(path.is_file() for path in specs_dir.glob("*.md"))
        print(f"Local Specs Detected: {os.path.relpath(specs_dir)} ({doc_count} documents)")
    elif specs_dir:
        print(f"Local Specs Path: Not a directory ({specs_dir})")
    else:
        print("Local Specs: None specified (using standard baseline)")
    print("=" * 60)

    results = [validate_file(Path(path).expanduser(), validator) for path in target_files]
    print("=" * 60)
    if all(results):
        print("ALL CONFIGURATIONS CONFORM TO SPECIFICATION")
        return 0

    print("VALIDATION FAILURES DETECTED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
