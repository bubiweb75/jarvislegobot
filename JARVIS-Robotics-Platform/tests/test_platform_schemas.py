#!/usr/bin/env python3
"""
JARVIS Robotics Platform — Automated Test Suite (RP-02)

Collauda l'intero patrimonio formale di FASE RP-02:
1. Validità sintattica dei 10 schemi JSON Draft 2020-12.
2. Validazione positiva di tutti i profili ufficiali (Skins, Identities, Voices, Wakewords, Hardware, Devices, Personalities).
3. Validazione positiva di tutte le fixture valide.
4. Convalida negativa e rigetto controllato di tutte le fixture invalide:
   - Mancanza espressione obbligatoria
   - Geometria oculare fuori scala rispetto a 128x64
   - Conflitto pin GPIO riservato (Octal PSRAM / Strapping)
   - Wake Word ACTIVE senza modello/checksum
   - Attacco Zip-Slip (path traversal ../)
   - Formato checksum SHA-256 alterato
5. Test semantico della matrice delle capacità tra profili hardware e identità.
"""

import sys
import json
import unittest
from pathlib import Path

# Aggiungi cartella validators al path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "validators"))

from validate_schemas import JSONSchemaEngine, validate_file
from validate_semantic import (
    validate_hardware_pinouts,
    validate_wakeword_consistency,
    validate_package_security,
    validate_skin_geometry,
    validate_capability_compatibility,
    run_semantic_checks,
    RESERVED_ESP32S3_PINS
)

class TestPlatformSchemas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas_dir = BASE_DIR / "schemas"
        cls.profiles_dir = BASE_DIR / "profiles"
        cls.fixtures_dir = BASE_DIR / "fixtures"
        cls.engine = JSONSchemaEngine(cls.schemas_dir)

    def test_01_all_schemas_exist_and_are_valid_json(self):
        """Tutti i 10 schemi JSON previsti devono esistere ed essere JSON valido."""
        expected_schemas = [
            "common.schema.json",
            "skin.schema.json",
            "identity.schema.json",
            "voice.schema.json",
            "wakeword.schema.json",
            "personality.schema.json",
            "hardware.schema.json",
            "device.schema.json",
            "capability.schema.json",
            "package.schema.json"
        ]
        for s_name in expected_schemas:
            s_path = self.schemas_dir / s_name
            self.assertTrue(s_path.is_file(), f"Schema mancante: {s_name}")
            with open(s_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data.get("$schema"), "https://json-schema.org/draft/2020-12/schema")
            self.assertIn("title", data)

    def test_02_official_skins_validation(self):
        """Tutte le 5 skin ufficiali devono superare la validazione sintattica e semantica."""
        skin_files = list((self.profiles_dir / "skins").glob("*.json"))
        self.assertGreaterEqual(len(skin_files), 5, "Devono essere presenti almeno 5 skin ufficiali")
        for skin_f in skin_files:
            ok, errors = validate_file(skin_f, self.engine, "skin.schema.json")
            self.assertTrue(ok, f"Validazione fallita per skin {skin_f.name}: {errors}")
            # Verifica semantica geometria
            with open(skin_f, "r", encoding="utf-8") as f:
                skin_data = json.load(f)
            geo_errors = validate_skin_geometry(skin_data)
            self.assertEqual(len(geo_errors), 0, f"Errori geometrici in {skin_f.name}: {geo_errors}")

    def test_03_official_identities_validation(self):
        """Tutte le 5 identità ufficiali devono superare la validazione dello schema."""
        id_files = list((self.profiles_dir / "identities").glob("*.json"))
        self.assertGreaterEqual(len(id_files), 5, "Devono essere presenti almeno 5 identità ufficiali")
        for id_f in id_files:
            ok, errors = validate_file(id_f, self.engine, "identity.schema.json")
            self.assertTrue(ok, f"Validazione fallita per identità {id_f.name}: {errors}")

    def test_04_official_voices_validation(self):
        """Tutti i profili vocali ufficiali devono superare la validazione dello schema."""
        voice_files = list((self.profiles_dir / "voices").glob("*.json"))
        self.assertGreaterEqual(len(voice_files), 3, "Devono essere presenti almeno 3 voci ufficiali")
        for voice_f in voice_files:
            ok, errors = validate_file(voice_f, self.engine, "voice.schema.json")
            self.assertTrue(ok, f"Validazione fallita per voce {voice_f.name}: {errors}")

    def test_05_official_wakewords_validation(self):
        """Tutti i profili wake word devono superare la validazione sintattica e semantica."""
        ww_files = list((self.profiles_dir / "wakewords").glob("*.json"))
        self.assertGreaterEqual(len(ww_files), 5, "Devono essere presenti almeno 5 profili wake word")
        for ww_f in ww_files:
            ok, errors = validate_file(ww_f, self.engine, "wakeword.schema.json")
            self.assertTrue(ok, f"Validazione fallita per wakeword {ww_f.name}: {errors}")
            with open(ww_f, "r", encoding="utf-8") as f:
                ww_data = json.load(f)
            sem_errors = validate_wakeword_consistency(ww_data)
            self.assertEqual(len(sem_errors), 0, f"Errori semantici in {ww_f.name}: {sem_errors}")

    def test_06_official_hardware_profiles_validation(self):
        """Tutti i profili hardware devono superare la validazione dello schema e il controllo pin."""
        hw_files = list((self.profiles_dir / "hardware").glob("*.json"))
        self.assertGreaterEqual(len(hw_files), 3, "Devono essere presenti almeno 3 profili hardware")
        for hw_f in hw_files:
            ok, errors = validate_file(hw_f, self.engine, "hardware.schema.json")
            self.assertTrue(ok, f"Validazione fallita per hardware {hw_f.name}: {errors}")
            with open(hw_f, "r", encoding="utf-8") as f:
                hw_data = json.load(f)
            pin_errors = validate_hardware_pinouts(hw_data)
            self.assertEqual(len(pin_errors), 0, f"Conflitti pin in {hw_f.name}: {pin_errors}")

    def test_07_official_personalities_and_devices_validation(self):
        """Tutte le personalità e i dispositivi devono essere formalmente validi."""
        pers_files = list((self.profiles_dir / "personalities").glob("*.json"))
        self.assertGreaterEqual(len(pers_files), 5, "Devono essere presenti almeno 5 personalità")
        for p_f in pers_files:
            ok, errors = validate_file(p_f, self.engine, "personality.schema.json")
            self.assertTrue(ok, f"Validazione fallita per personalità {p_f.name}: {errors}")

        dev_files = list((self.profiles_dir / "devices").glob("*.json"))
        self.assertGreaterEqual(len(dev_files), 1, "Deve essere presente almeno 1 profilo dispositivo")
        for d_f in dev_files:
            ok, errors = validate_file(d_f, self.engine, "device.schema.json")
            self.assertTrue(ok, f"Validazione fallita per device {d_f.name}: {errors}")

    def test_08_valid_fixtures_positive_testing(self):
        """Tutte le fixture valide devono passare senza errori sintattici o semantici."""
        valid_fixtures = [
            ("valid-skin.json", "skin.schema.json"),
            ("valid-identity.json", "identity.schema.json"),
            ("valid-hardware.json", "hardware.schema.json"),
            ("valid-package-manifest.json", "package.schema.json")
        ]
        for f_name, s_name in valid_fixtures:
            f_path = self.fixtures_dir / f_name
            ok, errors = validate_file(f_path, self.engine, s_name)
            self.assertTrue(ok, f"La fixture valida '{f_name}' è fallita: {errors}")
            sem_ok, sem_errs = run_semantic_checks(f_path)
            self.assertTrue(sem_ok, f"La fixture valida '{f_name}' ha fallito i controlli semantici: {sem_errs}")

    def test_09_negative_fixture_missing_expression(self):
        """Fixture negativa: rilevare la mancanza dell'espressione obbligatoria CONFUSED."""
        f_path = self.fixtures_dir / "invalid-skin-missing-expression.json"
        ok, errors = validate_file(f_path, self.engine, "skin.schema.json")
        self.assertFalse(ok, "La fixture con espressione mancante doveva fallire!")
        self.assertTrue(any("CONFUSED" in err for err in errors), f"Errore CONFUSED non rilevato: {errors}")

    def test_10_negative_fixture_out_of_bounds_geometry(self):
        """Fixture negativa: rilevare dimensioni oculari che eccedono l'inviluppo 128x64."""
        f_path = self.fixtures_dir / "invalid-skin-out-of-bounds.json"
        with open(f_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        geo_errors = validate_skin_geometry(data)
        self.assertGreater(len(geo_errors), 0, "I controlli di geometria dovevano rilevare il fuori scala!")

    def test_11_negative_fixture_reserved_pin_conflict(self):
        """Fixture negativa: rilevare assegnazione a GPIO 35 (riservato per Octal PSRAM)."""
        f_path = self.fixtures_dir / "invalid-hardware-psram-pin-conflict.json"
        with open(f_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        pin_errors = validate_hardware_pinouts(data)
        self.assertGreater(len(pin_errors), 0, "Il conflitto pin con GPIO 35 doveva essere rilevato!")
        self.assertTrue(any("GPIO 35" in err for err in pin_errors), f"Messaggio GPIO 35 non trovato: {pin_errors}")

    def test_12_negative_fixture_unverified_active_wakeword(self):
        """Fixture negativa: rilevare wake word marcata ACTIVE senza binario o checksum."""
        f_path = self.fixtures_dir / "invalid-wakeword-unverified-active.json"
        with open(f_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ww_errors = validate_wakeword_consistency(data)
        self.assertGreater(len(ww_errors), 0, "Wake word ACTIVE senza modello doveva fallire!")

    def test_13_negative_fixture_zipslip_attempt(self):
        """Fixture negativa: intercettare tentativo di path traversal Zip-Slip (../../)."""
        f_path = self.fixtures_dir / "invalid-package-zipslip-attempt.json"
        with open(f_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        sec_errors = validate_package_security(data)
        self.assertGreater(len(sec_errors), 0, "L'attacco Zip-Slip doveva essere bloccato!")
        self.assertTrue(any("Zip-Slip" in err for err in sec_errors), f"Allerta Zip-Slip non trovata: {sec_errors}")

    def test_14_negative_fixture_checksum_mismatch(self):
        """Fixture negativa: intercettare checksum SHA-256 non conforme."""
        f_path = self.fixtures_dir / "invalid-package-checksum-mismatch.json"
        with open(f_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        sec_errors = validate_package_security(data)
        self.assertGreater(len(sec_errors), 0, "Il checksum non valido doveva essere respinto!")

    def test_15_capability_matrix_matching(self):
        """Test di cross-validazione tra identità e profilo hardware."""
        with open(self.profiles_dir / "identities" / "jarvis.identity.json", "r", encoding="utf-8") as f:
            jarvis_id = json.load(f)
        with open(self.profiles_dir / "hardware" / "desktop-v1.hardware.json", "r", encoding="utf-8") as f:
            desktop_hw = json.load(f)

        # JARVIS Desktop soddisfa tutti i requisiti di JARVIS
        cap_errors = validate_capability_compatibility(jarvis_id, desktop_hw)
        self.assertEqual(len(cap_errors), 0, f"JARVIS deve essere compatibile con Desktop V1: {cap_errors}")

        # Se richiediamo una capacità non supportata (es. MOTOR_CONTROL)
        mock_rover_identity = dict(jarvis_id)
        mock_rover_identity["name"] = "Rover Bot"
        mock_rover_identity["required_capabilities"] = ["MOTOR_CONTROL", "CLIFF_DETECTION"]
        rover_cap_errors = validate_capability_compatibility(mock_rover_identity, desktop_hw)
        self.assertGreater(len(rover_cap_errors), 0, "Desktop V1 non ha la mobilità, doveva rilevare incompatibilità!")

if __name__ == "__main__":
    unittest.main(verbosity=2)
