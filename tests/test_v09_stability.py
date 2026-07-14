import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from expansion import (
    ExecutableExpansionPack,
    PackExecutionError,
    PackLoadError,
    PackLoader,
    PackManager,
    PackManifest,
    PackRegistry,
    PackRuntime,
    PackStateError,
)


class StabilityPack(ExecutableExpansionPack):
    def __init__(self, execute_hook=None, fail_execute=False, fail_terminate=False):
        self._manifest = PackManifest("stable", "Stable Pack", "1")
        self.execute_hook = execute_hook
        self.fail_execute = fail_execute
        self.fail_terminate = fail_terminate

    @property
    def manifest(self):
        return self._manifest

    def on_load(self):
        return None

    def on_unload(self):
        return None

    def execute(self, session):
        if self.execute_hook:
            self.execute_hook()
        if self.fail_execute:
            raise RuntimeError("private execute payload")

    def terminate(self, session):
        if self.fail_terminate:
            raise RuntimeError("private cleanup payload")


def make_lesson():
    return {
        "topic": "Python",
        "tutorial": "tutorial",
        "example": "example",
        "direct_task": "task",
        "practice": "practice",
        "difficulty": "Normal",
        "requested_question_count": 1,
        "cbt": [
            {
                "question": "Question",
                "choices": ["A", "B", "C", "D"],
                "answer_index": 0,
                "explanation": "explanation",
            }
        ],
    }


class RuntimeStabilityTests(unittest.TestCase):
    def test_execute_reentrant_unload_is_isolated(self):
        manager = PackManager()
        pack = StabilityPack(execute_hook=lambda: manager.unload("stable", "1"))
        manager.install(pack)
        manager.load("stable", "1")

        with self.assertRaises(PackExecutionError) as raised:
            manager.start("stable", "1")

        self.assertIsInstance(raised.exception.__cause__, PackStateError)
        self.assertTrue(manager.get("stable", "1").loaded)
        self.assertEqual(manager.sessions(), ())

    def test_direct_loader_cannot_unload_a_running_pack(self):
        registry = PackRegistry()
        loader = PackLoader(registry)
        runtime = PackRuntime(registry, loader)
        pack = StabilityPack()
        registry.register(pack)
        loader.load("stable", "1")
        status = runtime.start("stable", "1")

        with self.assertRaises(PackStateError):
            loader.unload("stable", "1")

        self.assertTrue(runtime.get(status.session_id).running)
        self.assertTrue(loader.is_loaded("stable", "1"))

    def test_cleanup_failure_is_structured_and_sanitized(self):
        manager = PackManager()
        pack = StabilityPack(fail_execute=True, fail_terminate=True)
        manager.install(pack)
        manager.load("stable", "1")

        with self.assertRaises(PackExecutionError) as raised:
            manager.start("stable", "1")

        error = raised.exception
        self.assertEqual(error.operation, "execute")
        self.assertEqual((error.pack_id, error.version), ("stable", "1"))
        self.assertTrue(error.cleanup_failed)
        self.assertNotIn("payload", str(error))
        self.assertEqual(manager.sessions(), ())

    def test_loader_error_has_stable_operation_context(self):
        registry = PackRegistry()
        loader = PackLoader(registry)
        pack = StabilityPack()
        pack.on_load = lambda: (_ for _ in ()).throw(RuntimeError("private payload"))
        registry.register(pack)

        with self.assertRaises(PackLoadError) as raised:
            loader.load("stable", "1")

        error = raised.exception
        self.assertEqual(error.operation, "load")
        self.assertEqual((error.pack_id, error.version), ("stable", "1"))
        self.assertNotIn("payload", str(error))


    def test_two_runtimes_cannot_start_the_same_loader_identity(self):
        registry = PackRegistry()
        loader = PackLoader(registry)
        first_runtime = PackRuntime(registry, loader)
        second_runtime = PackRuntime(registry, loader)
        pack = StabilityPack()
        registry.register(pack)
        loader.load("stable", "1")
        first_runtime.start("stable", "1")

        with self.assertRaises(PackStateError):
            second_runtime.start("stable", "1")

    def test_reentrant_stop_preserves_the_active_session(self):
        registry = PackRegistry()
        loader = PackLoader(registry)
        runtime = PackRuntime(registry, loader)
        pack = StabilityPack()
        registry.register(pack)
        loader.load("stable", "1")
        status = runtime.start("stable", "1")
        pack.fail_terminate = False
        original_terminate = pack.terminate

        def reentrant_terminate(session):
            pack.terminate = original_terminate
            runtime.stop(session.session_id)

        pack.terminate = reentrant_terminate
        with self.assertRaises(PackExecutionError) as raised:
            runtime.stop(status.session_id)

        self.assertIsInstance(raised.exception.__cause__, PackStateError)
        self.assertTrue(runtime.get(status.session_id).running)

class SessionStabilityTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file("app.py").run()
        self.assertFalse(self.app.exception)

    def test_corrupt_session_metadata_is_repaired_before_use(self):
        self.app.session_state["adaptation_records"] = "bad"
        self.app.session_state["analytics_revision"] = "bad"
        self.app.session_state["analytics_cache"] = []
        self.app.session_state["adaptation_error"] = "private payload"
        self.app.run()

        self.assertEqual(self.app.session_state["adaptation_records"], {})
        self.assertEqual(self.app.session_state["analytics_revision"], 0)
        self.assertIsNone(self.app.session_state["analytics_cache"])
        self.assertIsNone(self.app.session_state["adaptation_error"])
        self.assertFalse(self.app.exception)

    def test_adaptive_failure_does_not_partially_commit_round(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.session_state["answers"] = {0: 0}
        self.app.session_state["answer_confidence"] = {0: "high"}
        self.app.session_state["round_finished"] = True
        with patch(
            "adaptive.build_adaptive_summary", side_effect=RuntimeError("private payload")
        ):
            self.app.run()

        self.assertEqual(self.app.session_state["adaptation_records"], {})
        self.assertEqual(self.app.session_state["analytics_revision"], 0)
        self.assertEqual(self.app.session_state["analytics_cache"]["revision"], 0)
        self.assertIsNone(
            self.app.session_state["analytics_cache"]["result"]["latest_round"]
        )
        self.assertEqual(
            self.app.session_state["adaptation_error"], "adaptive_summary_failed"
        )
        self.assertFalse(self.app.exception)

    def test_corrupt_revision_is_repaired_before_atomic_commit(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.session_state["answers"] = {0: 0}
        self.app.session_state["answer_confidence"] = {0: "high"}
        self.app.session_state["round_finished"] = True
        self.app.session_state["analytics_revision"] = "bad"
        self.app.run()

        self.assertEqual(self.app.session_state["analytics_revision"], 1)
        self.assertEqual(len(self.app.session_state["adaptation_records"]["python"]), 1)
        self.assertFalse(self.app.exception)

    def test_retry_removes_answer_and_confidence_widget_state(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.session_state["answers"] = {0: 0}
        self.app.session_state["round_finished"] = True
        self.app.session_state["cbt_stale"] = 0
        self.app.session_state["confidence_stale"] = "high"
        self.app.run()
        retry = [item for item in self.app.button if item.label == "다시 학습"][0]
        retry.click().run()

        self.assertNotIn("cbt_stale", self.app.session_state)
        self.assertNotIn("confidence_stale", self.app.session_state)
        self.assertFalse(self.app.exception)


if __name__ == "__main__":
    unittest.main()
