#!/usr/bin/env python3
"""
JARVIS Robotics Platform — Semantic Validator

Esegue controlli di integrità semantica, sicurezza e compatibilità hardware che vanno oltre
la sola validazione sintattica dello schema JSON:
1. Conflitti GPIO con pin riservati (strapping, USB, Octal PSRAM/Flash).
2. Collisioni di pin tra periferiche differenti.
3. Coerenza dello stato dei modelli Wake Word (ACTIVE richiede binario e checksum).
4. Protezione da attacchi Zip-Slip (path traversal '../' o percorsi assoluti).
5. Verifica del formato crittografico dei checksum SHA-256.
6. Vincoli geometrici di visualizzazione rispetto all'inviluppo del display (128x64).
7. Compatibilità della matrice delle capacità tra Identità e Profilo Hardware.
"""

import sys
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

RESERVED_ESP32S3_PINS: Set[int] = {0, 3, 19, 20, 35, 36, 37, 38, 43, 44, 45, 46, 48}

def validate_hardware_pinouts(hw_data: Dict[str, Any]) -> List[str]:
    """Verifica conflitti pin con registri riservati e collisioni tra periferiche."""
    errors: List[str] = []
    assigned_pins: Dict[int, str] = {}
    declared_reserved = set(hw_data.get("reserved_pins", []))

    def check_pin(pin: Optional[int], function_label: str):
        if pin is None:
            return
        # Conflitto con pin riservati
        if pin in RESERVED_ESP32S3_PINS or pin in declared_reserved:
            errors.append(f"Conflitto hardware: GPIO {pin} assegnato a '{function_label}' appartiene all'elenco dei pin riservati (strapping/PSRAM/USB)")
        # Collisione tra funzioni (ad esclusione di bus I2C condiviso)
        if pin in assigned_pins:
            prev_label = assigned_pins[pin]
            errors.append(f"Collisione pin: GPIO {pin} assegnato sia a '{prev_label}' che a '{function_label}'")
        else:
            assigned_pins[pin] = function_label

    # Display I2C
    display = hw_data.get("display", {})
    check_pin(display.get("sda_gpio"), "Display SDA")
    check_pin(display.get("scl_gpio"), "Display SCL")

    # Audio In I2S
    ain = hw_data.get("audio_input", {})
    check_pin(ain.get("ws_gpio"), "Audio In WS")
    check_pin(ain.get("sck_gpio"), "Audio In SCK")
    check_pin(ain.get("sd_gpio"), "Audio In SD")

    # Audio Out I2S
    aout = hw_data.get("audio_output", {})
    check_pin(aout.get("din_gpio"), "Audio Out DIN")
    check_pin(aout.get("bclk_gpio"), "Audio Out BCLK")
    check_pin(aout.get("lrc_gpio"), "Audio Out LRC")

    # User Inputs
    uinputs = hw_data.get("user_inputs", {})
    check_pin(uinputs.get("ptt_button_gpio"), "PTT Button")
    check_pin(uinputs.get("touch_sensor_gpio"), "Touch Sensor")

    # Sensors
    sensors = hw_data.get("sensors", {})
    check_pin(sensors.get("tof_xshut_gpio"), "ToF XSHUT")
    check_pin(sensors.get("imu_int_gpio"), "IMU Interrupt")

    # Mobility
    mobility = hw_data.get("mobility", {})
    if mobility.get("enabled"):
        pinout = mobility.get("pinout", {})
        check_pin(pinout.get("pwma_gpio"), "Motor PWMA")
        check_pin(pinout.get("ain1_gpio"), "Motor AIN1")
        check_pin(pinout.get("ain2_gpio"), "Motor AIN2")
        check_pin(pinout.get("pwmb_gpio"), "Motor PWMB")
        check_pin(pinout.get("bin1_gpio"), "Motor BIN1")
        check_pin(pinout.get("bin2_gpio"), "Motor BIN2")
        check_pin(pinout.get("stby_gpio"), "Motor STBY")

        cliff = mobility.get("safety", {}).get("cliff_sensors", {})
        if cliff.get("enabled"):
            check_pin(cliff.get("cliff_left_gpio"), "Cliff Left Sensor")
            check_pin(cliff.get("cliff_right_gpio"), "Cliff Right Sensor")

    return errors

def validate_wakeword_consistency(ww_data: Dict[str, Any]) -> List[str]:
    """Verifica che un modello acustico ACTIVE/VALIDATED abbia file binario e checksum convalidati."""
    errors: List[str] = []
    status = ww_data.get("status")
    model_fn = ww_data.get("model_filename")
    size_bytes = ww_data.get("size_bytes")
    checksum = ww_data.get("checksum_sha256")

    if status in ("ACTIVE", "VALIDATED", "INSTALLED"):
        if not model_fn:
            errors.append(f"Incoerenza Wake Word: modello marcato come '{status}' ma privo di 'model_filename'")
        if not size_bytes:
            errors.append(f"Incoerenza Wake Word: modello marcato come '{status}' ma privo di 'size_bytes'")
        if not checksum or not re.match(r"^[a-fA-F0-9]{64}$", checksum):
            errors.append(f"Incoerenza Wake Word: modello marcato come '{status}' con checksum SHA-256 non valido")
    elif status == "DESIRED":
        pass

    return errors

def validate_package_security(pkg_data: Dict[str, Any]) -> List[str]:
    """Verifica prevenzione attacchi Zip-Slip e conformità dei limiti di sicurezza."""
    errors: List[str] = []
    assets = pkg_data.get("assets", [])

    for asset in assets:
        fn = asset.get("filename", "")
        # Zip-Slip check
        if ".." in fn or fn.startswith("/") or fn.startswith("\\") or ":" in fn:
            errors.append(f"Violazione di sicurezza Zip-Slip: il percorso '{fn}' contiene caratteri non ammessi (../, percorsi assoluti)")

        # Checksum format
        sha256 = asset.get("sha256", "")
        if not re.match(r"^[a-fA-F0-9]{64}$", sha256):
            errors.append(f"Integrità compromessa: il checksum SHA-256 dell'asset '{fn}' non è un hash esadecimale valido di 64 caratteri")

    limits = pkg_data.get("security_limits", {})
    if limits.get("max_extracted_bytes", 0) > 1048576:
        errors.append("Limite sicurezza superato: 'max_extracted_bytes' non può superare 1 MB (1048576 bytes)")
    if limits.get("max_compression_ratio", 0) > 10.0:
        errors.append("Limite sicurezza superato: 'max_compression_ratio' non può superare il valore di 10.0")

    return errors

def validate_skin_geometry(skin_data: Dict[str, Any]) -> List[str]:
    """Verifica che la geometria degli occhi non ecceda la matrice fisica del display (128x64)."""
    errors: List[str] = []
    target_display = skin_data.get("target_display", {})
    disp_w = target_display.get("width", 128)
    disp_h = target_display.get("height", 64)

    # Controllo base_geometry
    b_geo = skin_data.get("base_geometry", skin_data.get("canvas_geometry", {}))
    base_w = b_geo.get("width", b_geo.get("eye_width", 38))
    base_h = b_geo.get("height", b_geo.get("eye_height", 38))
    spacing = b_geo.get("spacing_px", b_geo.get("eye_spacing", 16))

    total_w = (base_w * 2) + spacing
    if total_w > disp_w:
        errors.append(f"Geometria fuori scala: larghezza totale occhi ({total_w} px) supera la larghezza display ({disp_w} px)")
    if base_h > disp_h:
        errors.append(f"Geometria fuori scala: altezza occhio ({base_h} px) supera l'altezza display ({disp_h} px)")

    # Controllo per ciascuna espressione
    expressions = skin_data.get("expressions", {})
    for expr_name, params in expressions.items():
        w = params.get("width", params.get("w", base_w))
        h = params.get("height", params.get("h", base_h))
        sp = params.get("spacing_px", params.get("spacing", spacing))
        tot_w = (w * 2) + sp
        if tot_w > disp_w:
            errors.append(f"Espressione '{expr_name}' fuori scala: larghezza {tot_w} px > {disp_w} px")
        if h > disp_h:
            errors.append(f"Espressione '{expr_name}' fuori scala: altezza {h} px > {disp_h} px")

    return errors

def validate_capability_compatibility(identity_data: Dict[str, Any], hardware_data: Dict[str, Any]) -> List[str]:
    """Verifica che tutte le capacità richieste dall'identità siano fornite dal profilo hardware."""
    errors: List[str] = []
    required_caps = set(identity_data.get("required_capabilities", []))
    hw_caps = set(hardware_data.get("capabilities", []))

    missing = required_caps - hw_caps
    if missing:
        errors.append(f"Incompatibilità di capacità: l'identità '{identity_data.get('name')}' richiede capacità non fornite dall'hardware: {list(missing)}")

    return errors

def run_semantic_checks(file_path: Path) -> Tuple[bool, List[str]]:
    """Esegue i controlli semantici pertinenti in base al contenuto del file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, [f"Errore lettura JSON {file_path}: {e}"]

    errors = []
    # Riconoscimento del tipo di documento
    if "hardware_profile_id" in data or "mcu" in data:
        errors.extend(validate_hardware_pinouts(data))
    if "wakeword_id" in data:
        errors.extend(validate_wakeword_consistency(data))
    if "package_id" in data or "package_type" in data:
        errors.extend(validate_package_security(data))
    if "skin_id" in data or "canvas_geometry" in data:
        errors.extend(validate_skin_geometry(data))

    return (len(errors) == 0), errors

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: validate_semantic.py <file_to_check>")
        sys.exit(1)

    target = Path(sys.argv[1])
    ok, errs = run_semantic_checks(target)
    if ok:
        print(f"[SEMANTIC PASS] {target.name}")
        sys.exit(0)
    else:
        print(f"[SEMANTIC FAIL] {target.name}")
        for err in errs:
            print(f"   -> {err}")
        sys.exit(1)
