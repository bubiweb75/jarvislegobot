#!/usr/bin/env python3
"""
JARVIS Robotics Platform — Schema Validator (Offline Draft 2020-12 Engine)

Valida documenti JSON contro gli schemi formali della piattaforma senza dipendenze esterne.
Supporta:
- $ref locali (#/$defs/...)
- $ref cross-file (common.schema.json#/$defs/...)
- type (object, array, string, integer, number, boolean)
- required properties
- additionalProperties: false
- enum, const
- minLength, maxLength, pattern (regex)
- minimum, maximum
- minItems, maxItems, uniqueItems
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

class SchemaValidationError(Exception):
    pass

class JSONSchemaEngine:
    def __init__(self, schemas_dir: Path):
        self.schemas_dir = schemas_dir
        self.loaded_schemas: Dict[str, Dict[str, Any]] = {}
        self._load_all_schemas()

    def _load_all_schemas(self):
        for schema_file in self.schemas_dir.glob("*.schema.json"):
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.loaded_schemas[schema_file.name] = data
            except Exception as e:
                print(f"[WARN] Impossibile caricare lo schema {schema_file}: {e}", file=sys.stderr)

    def resolve_ref(self, ref: str, current_schema: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Risolve un riferimento $ref interno o cross-file."""
        if "#" in ref:
            file_part, path_part = ref.split("#", 1)
        else:
            file_part, path_part = ref, ""

        if file_part:
            schema_name = Path(file_part).name
            if schema_name not in self.loaded_schemas:
                raise SchemaValidationError(f"Schema esterno non trovato: {schema_name}")
            target_schema = self.loaded_schemas[schema_name]
        else:
            target_schema = current_schema

        if not path_part or path_part == "/":
            return target_schema, target_schema

        parts = [p for p in path_part.strip("/").split("/") if p]
        curr = target_schema
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                raise SchemaValidationError(f"Riferimento $ref non risolvibile: {ref}")
        return curr, target_schema

    def validate(self, instance: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
        """Convalida un'istanza contro uno schema e restituisce la lista degli errori."""
        errors: List[str] = []
        self._validate_node(instance, schema, schema, path, errors)
        return errors

    def _validate_node(self, instance: Any, subschema: Dict[str, Any], root_schema: Dict[str, Any], path: str, errors: List[str]):
        if "$ref" in subschema:
            ref_subschema, new_root = self.resolve_ref(subschema["$ref"], root_schema)
            self._validate_node(instance, ref_subschema, new_root, path, errors)
            return

        # Controllo 'const'
        if "const" in subschema:
            if instance != subschema["const"]:
                errors.append(f"{path}: valore atteso '{subschema['const']}', ricevuto '{instance}'")

        # Controllo 'enum'
        if "enum" in subschema:
            if instance not in subschema["enum"]:
                errors.append(f"{path}: valore '{instance}' non presente nei valori ammessi {subschema['enum']}")

        # Controllo 'type'
        expected_type = subschema.get("type")
        if expected_type:
            if not self._check_type(instance, expected_type):
                errors.append(f"{path}: tipo non corrispondente (atteso '{expected_type}', ricevuto '{type(instance).__name__}')")
                return

        # Validazione specifica per tipo
        if isinstance(instance, dict):
            self._validate_object(instance, subschema, root_schema, path, errors)
        elif isinstance(instance, list):
            self._validate_array(instance, subschema, root_schema, path, errors)
        elif isinstance(instance, str):
            self._validate_string(instance, subschema, path, errors)
        elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
            self._validate_number(instance, subschema, path, errors)

    def _check_type(self, val: Any, expected: str) -> bool:
        if expected == "object":
            return isinstance(val, dict)
        if expected == "array":
            return isinstance(val, list)
        if expected == "string":
            return isinstance(val, str)
        if expected == "integer":
            return isinstance(val, int) and not isinstance(val, bool)
        if expected == "number":
            return (isinstance(val, (int, float))) and not isinstance(val, bool)
        if expected == "boolean":
            return isinstance(val, bool)
        if expected == "null":
            return val is None
        return True

    def _validate_object(self, obj: Dict[str, Any], subschema: Dict[str, Any], root_schema: Dict[str, Any], path: str, errors: List[str]):
        required = subschema.get("required", [])
        for req in required:
            if req not in obj:
                errors.append(f"{path}: proprietà obbligatoria mancante '{req}'")

        properties = subschema.get("properties", {})
        pattern_props = subschema.get("patternProperties", {})
        additional = subschema.get("additionalProperties", True)

        for key, val in obj.items():
            if key == "$schema" and path == "$":
                continue

            field_path = f"{path}.{key}"
            matched = False

            if key in properties:
                matched = True
                self._validate_node(val, properties[key], root_schema, field_path, errors)

            if pattern_props:
                for pat, pat_schema in pattern_props.items():
                    if re.search(pat, key):
                        matched = True
                        self._validate_node(val, pat_schema, root_schema, field_path, errors)

            if not matched:
                if additional is False:
                    errors.append(f"{path}: proprietà non ammessa '{key}' (additionalProperties: false)")
                elif isinstance(additional, dict):
                    self._validate_node(val, additional, root_schema, field_path, errors)

    def _validate_array(self, arr: List[Any], subschema: Dict[str, Any], root_schema: Dict[str, Any], path: str, errors: List[str]):
        min_items = subschema.get("minItems")
        if min_items is not None and len(arr) < min_items:
            errors.append(f"{path}: numero di elementi {len(arr)} inferiore al minimo {min_items}")

        max_items = subschema.get("maxItems")
        if max_items is not None and len(arr) > max_items:
            errors.append(f"{path}: numero di elementi {len(arr)} superiore al massimo {max_items}")

        if subschema.get("uniqueItems", False):
            # Controllo duplicati semplici
            serialized = [json.dumps(item, sort_keys=True) for item in arr]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{path}: contiene elementi duplicati (uniqueItems richiesto)")

        items_schema = subschema.get("items")
        if items_schema:
            for idx, item in enumerate(arr):
                self._validate_node(item, items_schema, root_schema, f"{path}[{idx}]", errors)

    def _validate_string(self, s: str, subschema: Dict[str, Any], path: str, errors: List[str]):
        min_len = subschema.get("minLength")
        if min_len is not None and len(s) < min_len:
            errors.append(f"{path}: lunghezza stringa {len(s)} inferiore al minimo {min_len}")

        max_len = subschema.get("maxLength")
        if max_len is not None and len(s) > max_len:
            errors.append(f"{path}: lunghezza stringa {len(s)} superiore al massimo {max_len}")

        pattern = subschema.get("pattern")
        if pattern is not None:
            if not re.search(pattern, s):
                errors.append(f"{path}: la stringa '{s}' non rispetta il pattern regex '{pattern}'")

    def _validate_number(self, n: float, subschema: Dict[str, Any], path: str, errors: List[str]):
        minimum = subschema.get("minimum")
        if minimum is not None and n < minimum:
            errors.append(f"{path}: valore {n} inferiore al minimo consentito {minimum}")

        maximum = subschema.get("maximum")
        if maximum is not None and n > maximum:
            errors.append(f"{path}: valore {n} superiore al massimo consentito {maximum}")

def validate_file(file_path: Path, engine: JSONSchemaEngine, schema_name: Optional[str] = None) -> Tuple[bool, List[str]]:
    """Convalida un file JSON contro lo schema specificato o rilevato tramite $schema."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, [f"Errore di parsing JSON nel file {file_path}: {e}"]

    target_schema_name = schema_name
    if not target_schema_name:
        schema_ref = data.get("$schema")
        if schema_ref:
            target_schema_name = Path(schema_ref).name
        else:
            return False, [f"Nessuno schema specificato e attributo '$schema' mancante in {file_path}"]

    if target_schema_name not in engine.loaded_schemas:
        return False, [f"Schema '{target_schema_name}' non trovato nella directory degli schemi"]

    schema = engine.loaded_schemas[target_schema_name]
    errors = engine.validate(data, schema)
    return (len(errors) == 0), errors

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: validate_schemas.py <file_or_dir_to_validate> [schema_name]")
        sys.exit(1)

    base_dir = Path(__file__).resolve().parent.parent
    schemas_directory = base_dir / "schemas"
    engine = JSONSchemaEngine(schemas_directory)

    target_path = Path(sys.argv[1])
    explicit_schema = sys.argv[2] if len(sys.argv) > 2 else None

    all_passed = True
    files_to_check = []
    if target_path.is_file():
        files_to_check.append(target_path)
    elif target_path.is_dir():
        files_to_check.extend(target_path.glob("**/*.json"))

    print(f"--- Convalida Schemi JSON (Motore Offline Draft 2020-12) ---")
    for f in files_to_check:
        ok, errs = validate_file(f, engine, explicit_schema)
        if ok:
            print(f"[PASS] {f.name}")
        else:
            print(f"[FAIL] {f.name}")
            for err in errs:
                print(f"   -> {err}")
            all_passed = False

    sys.exit(0 if all_passed else 1)
