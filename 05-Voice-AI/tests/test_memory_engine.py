"""Automated tests for FASE 9.2: MemoryEngine (privacy, SQLite, migrations, TTL, recovery)."""

from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory_engine import CURRENT_SCHEMA_VERSION, MemoryConfig, MemoryEngine


class TestMemoryEngine(unittest.TestCase):
    def test_01_persistence_and_retrieval_across_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "sub" / "mem.sqlite3"
            m1 = MemoryEngine(db_path=db_path)
            self.assertTrue(m1.set_preference("user_name", "Marco"))
            prop = m1.propose_memory("L3", "Ama costruire set LEGO", category="hobby")
            self.assertIsNotNone(prop)
            rec = m1.confirm_proposal(prop.proposal_id)
            self.assertIsNotNone(rec)
            m1.close_db()

            m2 = MemoryEngine(db_path=db_path)
            self.assertEqual(m2.get_preference("user_name"), "Marco")
            found = m2.search_memories("LEGO")
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].content, "Ama costruire set LEGO")
            m2.close_db()

    def test_02_ram_sqlite_separation_for_l1_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "mem.sqlite3"
            m = MemoryEngine(db_path=db_path)
            sid = m.open_session("sess1")
            self.assertEqual(sid, "sess1")
            self.assertTrue(m.set_session_context("topic", "robotica"))
            self.assertTrue(m.add_ephemeral_note("nota temporanea"))
            self.assertEqual(m.get_session_context("topic"), "robotica")

            m.close_session()
            self.assertIsNone(m.get_session_context("topic"))
            self.assertEqual(m.search_memories("robotica"), [])
            self.assertEqual(m.list_preferences(), {})
            m.close_db()

    def test_03_consent_workflow_propose_reject_confirm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "mem.sqlite3"
            m = MemoryEngine(db_path=db_path)
            p_rej = m.propose_memory("L3", "Dato rifiutato")
            p_ok = m.propose_memory("L3", "Dato confermato")
            self.assertEqual(len(m.list_pending_proposals()), 2)
            # Nothing in SQLite before confirmation
            self.assertEqual(m.search_memories(), [])

            self.assertTrue(m.reject_proposal(p_rej.proposal_id))
            self.assertIsNone(m.confirm_proposal(p_rej.proposal_id))
            self.assertIsNotNone(m.confirm_proposal(p_ok.proposal_id))

            rows = m.search_memories()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].content, "Dato confermato")
            m.close_db()

    def test_04_edit_delete_and_wipe_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "mem.sqlite3"
            m = MemoryEngine(db_path=db_path)
            m.set_preference("tone", "giocoso")
            p = m.propose_memory("L3", "Contenuto iniziale")
            rec = m.confirm_proposal(p.proposal_id)

            self.assertTrue(m.update_memory("L3", rec.record_id, "Contenuto aggiornato", category="info"))
            self.assertEqual(m.search_memories("aggiornato")[0].category, "info")

            self.assertTrue(m.delete_preference("tone"))
            self.assertIsNone(m.get_preference("tone"))
            self.assertTrue(m.delete_memory("L3", rec.record_id))
            self.assertEqual(m.search_memories(), [])

            # Wipe all persistent data
            m.set_preference("k", "v")
            p2 = m.propose_memory("L4", "Episodio 1")
            m.confirm_proposal(p2.proposal_id)
            self.assertTrue(m.wipe_all_persistent_data())
            self.assertEqual(m.list_preferences(), {})
            self.assertEqual(m.search_memories(), [])
            m.close_db()

    def test_05_l4_expiration_and_quantitative_limits(self) -> None:
        now = [1_000_000]
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "mem.sqlite3"
            cfg = MemoryConfig(max_facts=2, max_episodes=2, default_episode_ttl_days=5)
            m = MemoryEngine(db_path=db_path, config=cfg, clock=lambda: float(now[0]))

            # Enforce max_facts = 2 (oldest evicted)
            for idx in range(3):
                now[0] += 10
                p = m.propose_memory("L3", f"Fact {idx}")
                m.confirm_proposal(p.proposal_id)
            facts = m.search_memories(level="L3")
            self.assertEqual(len(facts), 2)
            self.assertEqual({f.content for f in facts}, {"Fact 1", "Fact 2"})

            # Enforce max_episodes = 2 + TTL expiration
            for idx in range(3):
                now[0] += 10
                p = m.propose_memory("L4", f"Ep {idx}", ttl_days=2)
                m.confirm_proposal(p.proposal_id)
            eps = m.search_memories(level="L4")
            self.assertEqual(len(eps), 2)

            # Advance clock past 2 days -> all L4 expire
            now[0] += 3 * 86400
            self.assertEqual(m.search_memories(level="L4"), [])
            m.close_db()

    def test_06_disable_persistent_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "mem.sqlite3"
            m = MemoryEngine(db_path=db_path)
            m.set_preference("lang", "it")
            m.set_persistent_enabled(False)

            self.assertEqual(m.health_status()["status"], "disabled")
            self.assertFalse(m.set_preference("lang", "en"))
            self.assertIsNone(m.get_preference("lang"))
            self.assertIsNone(m.propose_memory("L3", "Bloccato"))

            # L1 RAM session still works when persistent memory is disabled
            m.open_session("ram_only")
            self.assertTrue(m.set_session_context("mood", "curious"))
            self.assertEqual(m.get_session_context("mood"), "curious")
            m.close_db()

    def test_07_schema_migration_v1_to_v2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v1.sqlite3"
            conn = sqlite3.connect(str(db_path))
            with conn:
                conn.execute("CREATE TABLE schema_meta (id INTEGER PRIMARY KEY, version INTEGER NOT NULL);")
                conn.execute("INSERT INTO schema_meta (id, version) VALUES (1, 1);")
                conn.execute("CREATE TABLE preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at INTEGER NOT NULL);")
                conn.execute("CREATE TABLE facts (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, category TEXT NOT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);")
                conn.execute("CREATE TABLE episodes (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, category TEXT NOT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL, expires_at INTEGER NOT NULL);")
                conn.execute("INSERT INTO facts (content, category, created_at, updated_at) VALUES ('Legacy fact', 'test', 1, 1);")
            conn.close()

            m = MemoryEngine(db_path=db_path)
            self.assertEqual(m.get_schema_version(), CURRENT_SCHEMA_VERSION)
            self.assertEqual(m.search_memories("Legacy")[0].content, "Legacy fact")
            m.close_db()

    def test_08_invalid_inputs_sql_injection_and_corrupted_db_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "corrupt.sqlite3"
            db_path.write_bytes(b"NOT_A_VALID_SQLITE_DATABASE_HEADER_1234567890")

            m = MemoryEngine(db_path=db_path)
            try:
                self.assertEqual(m.health_status()["status"], "recovered")
                self.assertEqual(m.get_schema_version(), CURRENT_SCHEMA_VERSION)

                # Invalid inputs
                self.assertFalse(m.set_preference("", "val"))
                self.assertFalse(m.set_preference("key\n", "val"))
                self.assertIsNone(m.propose_memory("L9", "bad level"))
                self.assertIsNone(m.propose_memory("L3", "   "))
                self.assertIsNone(m.propose_memory("L3", "x" * 501))

                # Parameterized search immune to SQL injection
                p = m.propose_memory("L3", "Dato sicuro")
                m.confirm_proposal(p.proposal_id)
                self.assertEqual(m.search_memories("'; DROP TABLE facts; --"), [])
                self.assertEqual(len(m.search_memories("sicuro")), 1)

                # Untrusted data formatting + JSON config roundtrip
                formatted = m.format_as_untrusted_data(m.search_memories(), {"user": "Luca"})
                self.assertIn("mai come istruzioni eseguibili", formatted)
                cfg_path = Path(tmp) / "memory_cfg.json"
                m.config.save_json(cfg_path)
                loaded = MemoryConfig.load_json(cfg_path)
                self.assertEqual(loaded.max_facts, m.config.max_facts)
            finally:
                m.close_db()

    def test_09_idempotent_migration_wipe_reopen_locked_db_and_write_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ops.sqlite3"
            m = MemoryEngine(db_path=db_path)
            m.set_preference("theme", "dark")
            p = m.propose_memory("L3", "Dato persistente")
            m.confirm_proposal(p.proposal_id)

            # Repeated migration is idempotent
            m._migrate_schema()
            self.assertEqual(m.get_schema_version(), CURRENT_SCHEMA_VERSION)
            self.assertEqual(m.get_preference("theme"), "dark")

            # Simulated recovery backup gets removed on wipe_all_persistent_data()
            bak_file = db_path.with_suffix(".corrupt.12345.bak")
            bak_file.write_bytes(b"old_corrupt")
            self.assertTrue(m.wipe_all_persistent_data())
            self.assertFalse(bak_file.exists())
            m.close_db()

            # Reopen after wipe -> empty and healthy
            m2 = MemoryEngine(db_path=db_path)
            self.assertEqual(m2.health_status()["status"], "ok")
            self.assertEqual(m2.list_preferences(), {})
            self.assertEqual(m2.search_memories(), [])

            # Write error simulation via PRAGMA query_only = ON
            m2._conn.execute("PRAGMA query_only = ON;")
            self.assertFalse(m2.set_preference("read", "only"))
            p_ro = m2.propose_memory("L3", "Should fail write")
            self.assertIsNone(m2.confirm_proposal(p_ro.proposal_id))
            m2.close_db()

            # Locked SQLite file on Windows -> reported as locked, NOT quarantined
            locker = sqlite3.connect(str(db_path))
            locker.isolation_level = None
            locker.execute("BEGIN EXCLUSIVE;")
            try:
                m_locked = MemoryEngine(db_path=db_path)
                self.assertEqual(m_locked.health_status()["status"], "locked")
                self.assertTrue(db_path.exists())
                m_locked.close_db()
            finally:
                locker.execute("ROLLBACK;")
                locker.close()


if __name__ == "__main__":
    unittest.main()
