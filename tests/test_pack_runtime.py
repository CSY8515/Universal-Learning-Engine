import unittest
from dataclasses import FrozenInstanceError, fields

from expansion import (
    ExecutableExpansionPack,
    ExpansionAPI,
    ExpansionPack,
    PackContractError,
    PackExecutionError,
    PackLoadError,
    PackLoader,
    PackManifest,
    PackRegistry,
    PackRuntime,
    PackSessionNotFoundError,
    PackStateError,
)


class LegacyPack(ExpansionPack):
    def __init__(self, pack_id="legacy", version="1"):
        self._manifest = PackManifest(pack_id, f"{pack_id} pack", version)
        self.load_calls = 0
        self.unload_calls = 0

    @property
    def manifest(self):
        return self._manifest

    def on_load(self):
        self.load_calls += 1

    def on_unload(self):
        self.unload_calls += 1


class RuntimePack(ExecutableExpansionPack):
    def __init__(
        self,
        pack_id="runtime",
        version="1",
        fail_execute=False,
        fail_terminate=False,
        events=None,
    ):
        self._manifest = PackManifest(pack_id, f"{pack_id} pack", version)
        self.fail_execute = fail_execute
        self.fail_terminate = fail_terminate
        self.events = events if events is not None else []
        self.execute_sessions = []
        self.terminate_sessions = []

    @property
    def manifest(self):
        return self._manifest

    def on_load(self):
        self.events.append((self.manifest.identity, "load"))

    def on_unload(self):
        self.events.append((self.manifest.identity, "unload"))

    def execute(self, session):
        self.events.append((self.manifest.identity, "execute"))
        self.execute_sessions.append(session)
        session.state["owner"] = self.manifest.identity
        if self.fail_execute:
            raise RuntimeError("private execute payload")

    def terminate(self, session):
        self.events.append((self.manifest.identity, "terminate"))
        self.terminate_sessions.append(session)
        if self.fail_terminate:
            raise RuntimeError("private terminate payload")


class PackRuntimeTests(unittest.TestCase):
    def _loaded_api(self, pack):
        api = ExpansionAPI()
        api.install(pack)
        api.load(pack.manifest.pack_id, pack.manifest.version)
        return api

    def test_legacy_v07_pack_remains_manageable_but_not_executable(self):
        pack = LegacyPack()
        api = self._loaded_api(pack)
        self.assertTrue(api.get("legacy", "1").loaded)
        with self.assertRaises(PackContractError):
            api.start("legacy", "1")
        self.assertEqual(api.sessions(), ())
        self.assertFalse(api.unload("legacy", "1").loaded)
        self.assertEqual((pack.load_calls, pack.unload_calls), (1, 1))

    def test_start_requires_loaded_pack_and_returns_immutable_status(self):
        pack = RuntimePack()
        api = ExpansionAPI()
        api.install(pack)
        with self.assertRaises(PackStateError):
            api.start("runtime", "1")

        api.load("runtime", "1")
        status = api.start("runtime", "1")
        self.assertTrue(status.running)
        self.assertEqual((status.pack_id, status.version), ("runtime", "1"))
        with self.assertRaises(FrozenInstanceError):
            status.running = False
        with self.assertRaises(FrozenInstanceError):
            pack.execute_sessions[0].pack_id = "changed"
        self.assertEqual(api.session(status.session_id), status)

    def test_start_and_stop_use_the_same_private_session_once(self):
        pack = RuntimePack()
        api = self._loaded_api(pack)
        started = api.start("runtime", "1")
        stopped = api.stop(started.session_id)

        self.assertFalse(stopped.running)
        self.assertIs(pack.execute_sessions[0], pack.terminate_sessions[0])
        self.assertEqual(len(pack.execute_sessions), 1)
        self.assertEqual(len(pack.terminate_sessions), 1)
        self.assertEqual(api.sessions(), ())
        with self.assertRaises(PackSessionNotFoundError):
            api.session(started.session_id)

    def test_only_one_active_session_is_allowed_per_exact_identity(self):
        api = self._loaded_api(RuntimePack())
        api.start("runtime", "1")
        with self.assertRaises(PackStateError):
            api.start("runtime", "1")
        self.assertEqual(len(api.sessions()), 1)

    def test_execute_failure_is_cleaned_up_without_publishing_session(self):
        pack = RuntimePack(fail_execute=True)
        api = self._loaded_api(pack)
        with self.assertRaises(PackExecutionError) as raised:
            api.start("runtime", "1")
        self.assertNotIn("payload", str(raised.exception))
        self.assertEqual(len(pack.execute_sessions), 1)
        self.assertEqual(len(pack.terminate_sessions), 1)
        self.assertEqual(api.sessions(), ())
        self.assertTrue(api.get("runtime", "1").loaded)

    def test_terminate_failure_preserves_running_loaded_installed_state(self):
        pack = RuntimePack(fail_terminate=True)
        api = self._loaded_api(pack)
        status = api.start("runtime", "1")
        with self.assertRaises(PackExecutionError) as raised:
            api.stop(status.session_id)
        self.assertNotIn("payload", str(raised.exception))
        self.assertTrue(api.session(status.session_id).running)
        self.assertTrue(api.get("runtime", "1").loaded)
        self.assertEqual(len(api.list()), 1)

    def test_unload_terminates_session_before_pack_lifecycle_unload(self):
        events = []
        pack = RuntimePack(events=events)
        api = self._loaded_api(pack)
        api.start("runtime", "1")
        result = api.unload("runtime", "1")
        self.assertFalse(result.loaded)
        self.assertEqual(api.sessions(), ())
        self.assertEqual(
            [event for _, event in events],
            ["load", "execute", "terminate", "unload"],
        )

    def test_failed_termination_blocks_remove_without_partial_state_change(self):
        pack = RuntimePack(fail_terminate=True)
        api = self._loaded_api(pack)
        status = api.start("runtime", "1")
        with self.assertRaises(PackExecutionError):
            api.remove("runtime", "1")
        self.assertTrue(api.session(status.session_id).running)
        self.assertTrue(api.get("runtime", "1").loaded)

    def test_packs_and_exact_versions_receive_separate_session_state(self):
        first = RuntimePack("alpha", "1")
        second = RuntimePack("alpha", "2")
        third = RuntimePack("beta", "1")
        api = ExpansionAPI()
        for pack in (third, second, first):
            api.install(pack)
            api.load(pack.manifest.pack_id, pack.manifest.version)
            api.start(pack.manifest.pack_id, pack.manifest.version)

        sessions = [pack.execute_sessions[0] for pack in (first, second, third)]
        self.assertEqual(len({id(session) for session in sessions}), 3)
        self.assertEqual(len({id(session.state) for session in sessions}), 3)
        sessions[0].state["private"] = "alpha-1"
        self.assertNotIn("private", sessions[1].state)
        self.assertNotIn("private", sessions[2].state)
        self.assertEqual(
            [(item.pack_id, item.version) for item in api.sessions()],
            [("alpha", "1"), ("alpha", "2"), ("beta", "1")],
        )

    def test_public_session_status_does_not_expose_private_state(self):
        api = self._loaded_api(RuntimePack())
        status = api.start("runtime", "1")
        self.assertNotIn("state", {field.name for field in fields(status)})
        self.assertFalse(hasattr(status, "state"))
        with self.assertRaises(PackContractError):
            api.stop("  ")
        with self.assertRaises(PackSessionNotFoundError):
            api.stop("missing")

    def test_loader_rejects_reentrant_lifecycle_transitions(self):
        registry = PackRegistry()
        pack = LegacyPack()
        registry.register(pack)
        loader = PackLoader(registry)

        pack.on_load = lambda: loader.load("legacy", "1")
        with self.assertRaises(PackLoadError):
            loader.load("legacy", "1")
        self.assertFalse(loader.is_loaded("legacy", "1"))

        pack.on_load = lambda: None
        loader.load("legacy", "1")
        pack.on_unload = lambda: loader.unload("legacy", "1")
        with self.assertRaises(PackLoadError):
            loader.unload("legacy", "1")
        self.assertTrue(loader.is_loaded("legacy", "1"))

    def test_runtime_rejects_a_loader_owned_by_another_registry(self):
        registry = PackRegistry()
        other_registry = PackRegistry()
        with self.assertRaises(ValueError):
            PackRuntime(registry, PackLoader(other_registry))


if __name__ == "__main__":
    unittest.main()
