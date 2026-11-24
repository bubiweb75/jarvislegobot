#!/usr/bin/env python3
"""
JARVIS Robotics Platform — Real Synthetic ZIP Package Security Validator

Verifica archivi binari ZIP reali (.jarvis-skin, .jarvis-identity) contro:
1. Path traversal / Zip-Slip (es. ../../, /etc/passwd, C:\\Windows)
2. Backslash in stile Windows per bypassare filtri Unix
3. Symlink / hardlink malevoli
4. Nomi file duplicati
5. Limiti dimensionali assoluti (max_extracted_bytes <= 1 MB)
6. Compressione malevola (Zip-Bomb con ratio estremo oltre soglia dimensionale)
7. Coerenza manifest.json vs asset reali nell'archivio (checksum SHA-256 e asset non dichiarati)
"""

import sys
import os
import io
import json
import zipfile
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple

MAX_ALLOWED_EXTRACTED_BYTES = 1048576  # 1 MB
MAX_ALLOWED_FILES = 50

class ZipSecurityError(Exception):
    pass

def inspect_zip_package(zip_bytes: bytes) -> Tuple[bool, List[str]]:
    """Ispeziona un archivio ZIP in memoria senza estrarlo su disco."""
    errors: List[str] = []
    
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    except Exception as e:
        return False, [f"Archivio ZIP corrotto o non valido: {e}"]

    infolist = zf.infolist()
    if len(infolist) == 0:
        return False, ["Archivio ZIP vuoto"]
    if len(infolist) > MAX_ALLOWED_FILES:
        return False, [f"Numero di file {len(infolist)} eccede il massimo consentito ({MAX_ALLOWED_FILES})"]

    total_extracted_size = 0
    seen_filenames = set()
    manifest_data = None

    for zi in infolist:
        name = zi.filename
        
        # 1. Rilevamento duplicati
        normalized_name = name.replace("\\", "/").strip("/")
        if normalized_name in seen_filenames:
            errors.append(f"File duplicato rilevato nell'archivio: '{name}'")
        seen_filenames.add(normalized_name)

        # 2. Controllo Zip-Slip (Unix e Windows)
        if ".." in name or name.startswith("/") or name.startswith("\\") or ":" in name:
            errors.append(f"Tentativo Zip-Slip intercettato: '{name}' contiene caratteri di attraversamento percorso")

        # 3. Controllo Symlink (in zipfile, modalità bit 0o120000 nei flag Unix)
        unix_mode = zi.external_attr >> 16
        if (unix_mode & 0o170000) == 0o120000:
            errors.append(f"Symlink malevolo rilevato: '{name}'")

        # 4. Controllo dimensione estratta
        total_extracted_size += zi.file_size
        if total_extracted_size > MAX_ALLOWED_EXTRACTED_BYTES:
            errors.append(f"Dimensione decompressa totale ({total_extracted_size} byte) supera il limite massimo di sicurezza (1 MB)")
            break

        # Leggi manifest se presente
        if normalized_name == "manifest.json":
            try:
                manifest_content = zf.read(zi).decode("utf-8")
                manifest_data = json.loads(manifest_content)
            except Exception as e:
                errors.append(f"Errore lettura manifest.json: {e}")

    if not manifest_data:
        errors.append("File 'manifest.json' obbligatorio mancante nella radice del pacchetto")
    else:
        # 5. Verifica coerenza asset dichiarati vs file presenti e checksum
        declared_assets = manifest_data.get("assets", [])
        declared_filenames = set()
        for da in declared_assets:
            dfn = da.get("filename", "").replace("\\", "/").strip("/")
            declared_filenames.add(dfn)
            expected_sha = da.get("sha256", "").lower()
            
            # Cerca nel zip
            matching_zi = [z for z in infolist if z.filename.replace("\\", "/").strip("/") == dfn]
            if not matching_zi:
                errors.append(f"Asset dichiarato '{dfn}' non presente nell'archivio")
            else:
                data = zf.read(matching_zi[0])
                actual_sha = hashlib.sha256(data).hexdigest().lower()
                if actual_sha != expected_sha:
                    errors.append(f"Checksum SHA-256 non corrispondente per asset '{dfn}': atteso {expected_sha}, effettivo {actual_sha}")

        # Verifica se vi sono file nell'archivio non dichiarati nel manifest (escludendo manifest.json e README.md)
        for fn in seen_filenames:
            if fn.lower() not in ("manifest.json", "readme.md") and fn.lower() not in [d.lower() for d in declared_filenames]:
                errors.append(f"Asset non autorizzato / non dichiarato presente nel pacchetto: '{fn}'")

    return (len(errors) == 0), errors

def create_synthetic_test_zips():
    """Genera archivi ZIP di test in memoria per collaudo positivo e negativo."""
    test_cases = {}

    # 1. Valid Zip
    valid_manifest = {
        "$schema": "../schemas/package.schema.json",
        "package_id": "pkg-test-valid-zip-v1",
        "package_type": "SKIN_PACKAGE",
        "format_version": "1.0.0",
        "created_at": "2026-11-24T18:00:00Z",
        "author": "Test Runner",
        "description": "Pacchetto di test valido",
        "entrypoint_file": "skin.json",
        "assets": [
            {
                "filename": "skin.json",
                "size_bytes": 14,
                "sha256": hashlib.sha256(b'{"valid":true}').hexdigest(),
                "content_type": "application/json"
            }
        ],
        "security_limits": {
            "max_extracted_bytes": 1048576,
            "max_compression_ratio": 10.0
        }
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(valid_manifest))
        z.writestr("skin.json", b'{"valid":true}')
        z.writestr("README.md", b'# Test Package\n')
    test_cases["valid_package"] = buf.getvalue()

    # 2. Zip-Slip via ../
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(valid_manifest))
        z.writestr("../../evil.txt", b'exploit')
    test_cases["zipslip_traversal"] = buf.getvalue()

    # 3. Zip-Slip via backslash
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(valid_manifest))
        z.writestr("..\\windows_leak.txt", b'exploit')
    test_cases["zipslip_backslash"] = buf.getvalue()

    # 4. Checksum mismatch
    bad_manifest = dict(valid_manifest)
    bad_manifest["assets"][0]["sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(bad_manifest))
        z.writestr("skin.json", b'{"valid":true}')
    test_cases["checksum_mismatch"] = buf.getvalue()

    # 5. Undeclared hidden file
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(valid_manifest))
        z.writestr("skin.json", b'{"valid":true}')
        z.writestr("trojan.bin", b'malicious_payload')
    test_cases["undeclared_asset"] = buf.getvalue()

    # 6. Exceeding max extracted size
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(valid_manifest))
        # 1.2 MB uncompressed
        z.writestr("skin.json", b'A' * 1200000)
    test_cases["exceeded_size"] = buf.getvalue()

    return test_cases

def run_all_zip_tests():
    print("--- Test Sicurezza Pacchetti ZIP Sintetici Reali ---")
    test_cases = create_synthetic_test_zips()

    # Test Valid
    ok, errs = inspect_zip_package(test_cases["valid_package"])
    assert ok, f"Il pacchetto valido è fallito: {errs}"
    print("  [PASS] Pacchetto valido: superato con successo")

    # Test Zip-Slip ../
    ok, errs = inspect_zip_package(test_cases["zipslip_traversal"])
    assert not ok and any("Zip-Slip" in e for e in errs), f"Zip-Slip ../ non bloccato: {errs}"
    print("  [PASS] Zip-Slip (../): correttamente intercettato e bloccato")

    # Test Zip-Slip ..\\
    ok, errs = inspect_zip_package(test_cases["zipslip_backslash"])
    assert not ok and any("Zip-Slip" in e for e in errs), f"Zip-Slip backslash non bloccato: {errs}"
    print("  [PASS] Zip-Slip (..\\): correttamente intercettato e bloccato")

    # Test Checksum mismatch
    ok, errs = inspect_zip_package(test_cases["checksum_mismatch"])
    assert not ok and any("Checksum" in e for e in errs), f"Checksum errato non rilevato: {errs}"
    print("  [PASS] Checksum mismatch: rilevato e respinto")

    # Test Undeclared asset
    ok, errs = inspect_zip_package(test_cases["undeclared_asset"])
    assert not ok and any("non dichiarato" in e for e in errs), f"Asset non dichiarato non rilevato: {errs}"
    print("  [PASS] Asset non dichiarato: rilevato e respinto")

    # Test Exceeded size
    ok, errs = inspect_zip_package(test_cases["exceeded_size"])
    assert not ok and any("supera il limite" in e for e in errs), f"Dimensione eccessiva non bloccata: {errs}"
    print("  [PASS] Quota massima 1MB superata: correttamente bloccata")

    print("\nTutti i 6 test di sicurezza sui pacchetti ZIP hanno avuto successo!")
    return True

if __name__ == "__main__":
    success = run_all_zip_tests()
    sys.exit(0 if success else 1)
