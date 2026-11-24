#!/usr/bin/env python3
"""
JARVIS Robotics Platform — Standard JSON Schema Draft 2020-12 Validator

Utilizza la libreria standard 'jsonschema' (Draft202012Validator) con 'referencing'
per validare formalmente tutti gli schemi, i profili e le fixture della piattaforma.
"""

import sys
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = BASE_DIR / "schemas"
PROFILES_DIR = BASE_DIR / "profiles"
FIXTURES_DIR = BASE_DIR / "fixtures"

def build_schema_registry():
    """Costruisce il registro delle risorse referencing per risolvere $ref cross-file."""
    resources = []
    schema_map = {}
    for sf in SCHEMAS_DIR.glob("*.schema.json"):
        with open(sf, "r", encoding="utf-8") as f:
            data = json.load(f)
            schema_map[sf.name] = data
            res = Resource.from_contents(data)
            # Aggiungi sia con URI $id che con nome file relativo
            schema_id = data.get("$id", f"https://jarvis-platform.local/schemas/{sf.name}")
            resources.append((schema_id, res))
            resources.append((sf.name, res))
            resources.append((f"../../schemas/{sf.name}", res))
            resources.append((f"../schemas/{sf.name}", res))

    registry = Registry().with_resources(resources)
    return registry, schema_map

def validate_all():
    print("--- Avvio Convalida Formale con jsonschema.Draft202012Validator ---")
    registry, schema_map = build_schema_registry()

    # 1. Verifica validità di ciascun schema rispetto al metaschema
    print("\n[1/3] Verifica validità degli schemi...")
    for s_name, s_data in schema_map.items():
        try:
            Draft202012Validator.check_schema(s_data)
            print(f"  [OK] {s_name} conforme a Draft 2020-12")
        except Exception as e:
            print(f"  [FAIL] {s_name}: {e}")
            return False

    # 2. Convalida di tutti i profili ufficiali
    print("\n[2/3] Convalida di tutti i 27 profili ufficiali...")
    profile_mappings = {
        "skins": "skin.schema.json",
        "identities": "identity.schema.json",
        "personalities": "personality.schema.json",
        "voices": "voice.schema.json",
        "wakewords": "wakeword.schema.json",
        "hardware": "hardware.schema.json",
        "devices": "device.schema.json"
    }

    all_passed = True
    total_profiles = 0
    for subdir, schema_name in profile_mappings.items():
        folder = PROFILES_DIR / subdir
        schema_data = schema_map[schema_name]
        validator = Draft202012Validator(schema_data, registry=registry)

        files = list(folder.glob("*.json"))
        total_profiles += len(files)
        for pf in files:
            with open(pf, "r", encoding="utf-8") as f:
                instance = json.load(f)
            errors = list(validator.iter_errors(instance))
            if not errors:
                print(f"  [PASS] {subdir}/{pf.name}")
            else:
                print(f"  [FAIL] {subdir}/{pf.name}:")
                for err in errors:
                    print(f"     -> {err.message} (percorso: {list(err.path)})")
                all_passed = False

    print(f"\nTotale profili ufficiali verificati: {total_profiles}")

    # 3. Convalida fixture valide
    print("\n[3/3] Convalida fixture valide...")
    fixtures = [
        ("valid-skin.json", "skin.schema.json"),
        ("valid-identity.json", "identity.schema.json"),
        ("valid-hardware.json", "hardware.schema.json"),
        ("valid-package-manifest.json", "package.schema.json")
    ]
    for fix_name, s_name in fixtures:
        fp = FIXTURES_DIR / fix_name
        schema_data = schema_map[s_name]
        validator = Draft202012Validator(schema_data, registry=registry)
        with open(fp, "r", encoding="utf-8") as f:
            instance = json.load(f)
        errors = list(validator.iter_errors(instance))
        if not errors:
            print(f"  [PASS] fixture/{fix_name}")
        else:
            print(f"  [FAIL] fixture/{fix_name}:")
            for err in errors:
                print(f"     -> {err.message}")
            all_passed = False

    return all_passed

if __name__ == "__main__":
    ok = validate_all()
    sys.exit(0 if ok else 1)
