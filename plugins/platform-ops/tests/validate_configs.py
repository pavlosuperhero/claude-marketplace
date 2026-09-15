#!/usr/bin/env python3
"""
ZIPPO Specification & Config Validator
Validates application YAML configurations against zippo-specs JSON schemas.
Uses built-in standard library + PyYAML from venv if present, with fallback parser.
"""

import sys
import os
import re
import json

try:
    import yaml
except ImportError:
    # Search parent directories for a virtualenv containing PyYAML
    cur = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        for sub in ["ZIPPO-INFR/.venv/bin/python3", ".venv/bin/python3"]:
            candidate = os.path.join(cur, sub)
            if os.path.exists(candidate) and sys.executable != os.path.abspath(candidate):
                os.execv(candidate, [candidate] + sys.argv)
        cur = os.path.dirname(cur)
    raise


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

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    schema_path = os.path.join(base_dir, "schemas/app-config.schema.json")
    
    with open(schema_path, "r") as f:
        schema = json.load(f)

    test_files = [
        os.path.abspath(os.path.join(base_dir, "../ZIPPO-BE/deploy/dev/config.yaml")),
        os.path.abspath(os.path.join(base_dir, "../ZIPPO-FE/deploy/dev/config.yaml"))
    ]
    
    # Also validate any file passed as CLI argument
    if len(sys.argv) > 1:
        test_files = [os.path.abspath(f) for f in sys.argv[1:]]

    all_passed = True
    print("=" * 60)
    print("ZIPPO SPEC-DRIVEN DEVELOPMENT: CONFIG VALIDATOR")
    print(f"Schema: {os.path.relpath(schema_path)}")
    print("=" * 60)

    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"[-] SKIPPED: {file_path} not found")
            continue
        try:
            with open(file_path, "r") as f:
                config_data = yaml.safe_load(f)
            
            # Normalize uppercase keys if needed
            errors = validate_schema(config_data, schema, path="config")
            
            if not errors:
                print(f"[✓] PASSED: {os.path.relpath(file_path)}")
            else:
                all_passed = False
                print(f"[✗] FAILED: {os.path.relpath(file_path)}")
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
