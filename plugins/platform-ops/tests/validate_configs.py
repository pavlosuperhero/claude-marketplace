#!/usr/bin/env python3
# /// script
# dependencies = [
#     "pyyaml",
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

import sys
import os
import re
import json
import argparse
import yaml

def validate_schema(instance, schema, path="root"):
    errors = []
    
    # Check type
    expected_type = schema.get("type")
    if expected_type:
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list,
        }
        if expected_type == "integer" and isinstance(instance, bool):
            errors.append(f"{path}: expected integer, got boolean")
            return errors
        if expected_type in type_map and not isinstance(instance, type_map[expected_type]):
            errors.append(f"{path}: expected {expected_type}, got {type(instance).__name__}")
            return errors

    # Check enums
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value '{instance}' not in allowed enums: {schema['enum']}")

    # String validations
    if isinstance(instance, str):
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: string '{instance}' does not match pattern {schema['pattern']}")

    # Number validations
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} is less than minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: {instance} is greater than maximum {schema['maximum']}")

    # Array validations
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: items count {len(instance)} less than minItems {schema['minItems']}")
        if "items" in schema:
            for idx, item in enumerate(instance):
                errors.extend(validate_schema(item, schema["items"], f"{path}[{idx}]"))

    # Object validations
    if isinstance(instance, dict):
        required_props = schema.get("required", [])
        for req in required_props:
            if req not in instance:
                errors.append(f"{path}: missing required property '{req}'")
        
        properties = schema.get("properties", {})
        additional_allowed = schema.get("additionalProperties", True)

        for key, value in instance.items():
            if key in properties:
                errors.extend(validate_schema(value, properties[key], f"{path}.{key}"))
            elif additional_allowed is False:
                errors.append(f"{path}: unexpected additional property '{key}'")
            elif isinstance(additional_allowed, dict):
                errors.extend(validate_schema(value, additional_allowed, f"{path}.{key}"))

    return errors

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
        help="Path to the JSON schema file to validate against."
    )
    parser.add_argument(
        "-d", "--specs-dir",
        dest="specs_dir",
        default=os.environ.get("ADDITIONAL_SPECS_PATH") or os.environ.get("PROJECT_SPECS_PATH"),
        help="Path to additional local specifications on PC to cross-reference (or env ADDITIONAL_SPECS_PATH)."
    )
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
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Resolve schema path based on --schema-type or explicit --schema
    schema_type_map = {
        "app": "app-config.schema.json",
        "environment": "environment.schema.json",
        "service": "service-spec.schema.json",
    }
    default_schema = os.path.abspath(os.path.join(script_dir, "../schemas", schema_type_map[args.schema_type]))
    schema_path = args.schema_path or default_schema

    if not os.path.exists(schema_path):
        print(f"Error: Schema file not found: {schema_path}", file=sys.stderr)
        sys.exit(1)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    target_files = list(args.files)
    if args.single_config:
        target_files.append(args.single_config)

    if not target_files:
        print("Usage: uv run tests/validate_configs.py <path-to-config.yaml> [--schema <schema.json>]")
        sys.exit(1)

    all_passed = True
    print("=" * 60)
    print("SPEC-DRIVEN DEVELOPMENT: CONFIG VALIDATOR")
    print(f"Schema: {os.path.relpath(schema_path)}")

    # Check for additional local specifications
    specs_dir = args.specs_dir
    if not specs_dir:
        candidates = [
            os.path.abspath("Project_Specifications"),
            os.path.abspath("../Project_Specifications"),
            os.path.abspath("../../Project_Specifications"),
            os.path.abspath("../../../Project_Specifications"),
            os.path.abspath("zippo-specs"),
            os.path.abspath("../zippo-specs"),
        ]
        for c in candidates:
            if os.path.isdir(c) and any(f.endswith(".md") for f in os.listdir(c)):
                specs_dir = c
                break

    if specs_dir and os.path.isdir(specs_dir):
        doc_count = len([f for f in os.listdir(specs_dir) if f.endswith(".md")])
        print(f"Local Specs Detected: {os.path.relpath(specs_dir)} ({doc_count} documents)")
    elif specs_dir and not os.path.exists(specs_dir):
        print(f"Local Specs Path: Not found ({specs_dir})")
    else:
        print("Local Specs: None specified (using standard baseline)")
    print("=" * 60)

    for file_path in target_files:
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            print(f"[-] SKIPPED: {file_path} not found")
            continue
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            
            errors = validate_schema(config_data, schema, path="config")
            
            if not errors:
                print(f"[✓] PASSED: {os.path.relpath(abs_path)}")
            else:
                all_passed = False
                print(f"[✗] FAILED: {os.path.relpath(abs_path)}")
                for err in errors:
                    print(f"    - {err}")
        except Exception as e:
            all_passed = False
            print(f"[✗] ERROR: {file_path}: {e}")

    print("=" * 60)
    if all_passed:
        print("ALL CONFIGURATIONS CONFORM TO SPECIFICATION")
        sys.exit(0)
    else:
        print("VALIDATION FAILURES DETECTED")
        sys.exit(1)

if __name__ == "__main__":
    main()
