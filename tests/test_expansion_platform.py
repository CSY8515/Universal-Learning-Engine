import inspect
import unittest

from expansion import (
    AmbiguousPackVersionError,
    DuplicatePackError,
    ExpansionAPI,
    ExpansionPack,
    IncompatiblePackError,
    LivingOSIntegrationInterface,
    PackContractError,
    PackLoadError,
    PackLoader,
    PackManager,
    PackManifest,
    PackRegistry,
    PackStateError,
)


class ExamplePack(ExpansionPack):
    def __init__(
        self,
        pack_id="example",
        version="1.0",
        interface_version="0.7",
        fail_load=False,
        fail_unload=False,
    ):
        self._manifest = PackManifest(
            pack_id=pack_id,
            name=f"{pack_id} pack",
            version=version,
            interface_version=interface_version,
        )
        self.fail_load = fail_load
        self.fail_unload = fail_unload
        self.load_calls = 0
        self.unload_calls = 0

    @property
    def manifest(self):
        return self._manifest

    def on_load(self):
        self.load_calls += 1
        if self.fail_load:
            raise RuntimeError("load payload must stay internal")

    def on_unload(self):
        self.unload_calls += 1
        if self.fail_unload:
            raise RuntimeError("unload payload must stay internal")


class ExpansionPlatformTests(unittest.TestCase):
    def test_manifest_is_immutable_and_validated(self):
        manifest = PackManifest(" pack ", " Pack ", " 1.0 ")
        self.assertEqual(manifest.identity, ("pack", "1.0"))
        with self.assertRaises(PackContractError):
            PackManifest("", "Pack", "1.0")
        with self.assertRaises(Exception) as raised:
            manifest.version = "2.0"
        self.assertEqual(type(raised.exception).__name__, "FrozenInstanceError")

    def test_pack_contract_and_interface_version_are_enforced(self):
        with self.assertRaises(PackContractError):
            PackManager().install(object())
        with self.assertRaises(IncompatiblePackError):
            PackManager().install(ExamplePack(interface_version="0.8"))

    def test_registry_uses_exact_identity_and_rejects_duplicates(self):
        registry = PackRegistry()
        first = ExamplePack("alpha", "1")
        registry.register(first)
        with self.assertRaises(DuplicatePackError):
            registry.register(ExamplePack("alpha", "1"))
        self.assertIs(registry.get("alpha", "1"), first)

    def test_registry_requires_version_when_multiple_are_installed(self):
        registry = PackRegistry()
        registry.register(ExamplePack("alpha", "2"))
        registry.register(ExamplePack("alpha", "1"))
        with self.assertRaises(AmbiguousPackVersionError):
            registry.get("alpha")
        self.assertEqual(registry.versions("alpha"), ("1", "2"))
        self.assertEqual(
            [manifest.identity for manifest in registry.manifests()],
            [("alpha", "1"), ("alpha", "2")],
        )

    def test_loader_invokes_each_lifecycle_operation_once(self):
        registry = PackRegistry()
        pack = ExamplePack()
        registry.register(pack)
        loader = PackLoader(registry)

        loader.load("example", "1.0")
        self.assertTrue(loader.is_loaded("example", "1.0"))
        self.assertEqual(pack.load_calls, 1)
        with self.assertRaises(PackStateError):
            loader.load("example", "1.0")

        loader.unload("example", "1.0")
        self.assertFalse(loader.is_loaded("example", "1.0"))
        self.assertEqual(pack.unload_calls, 1)

    def test_load_failure_does_not_mark_pack_loaded(self):
        registry = PackRegistry()
        registry.register(ExamplePack(fail_load=True))
        loader = PackLoader(registry)
        with self.assertRaises(PackLoadError) as raised:
            loader.load("example", "1.0")
        self.assertNotIn("payload", str(raised.exception))
        self.assertFalse(loader.is_loaded("example", "1.0"))

    def test_installed_manifest_cannot_change_before_load(self):
        registry = PackRegistry()
        pack = ExamplePack()
        registry.register(pack)
        pack._manifest = PackManifest("example", "changed", "1.0")
        loader = PackLoader(registry)
        with self.assertRaises(PackContractError):
            loader.load("example", "1.0")
        self.assertFalse(loader.is_loaded("example", "1.0"))

    def test_unload_failure_preserves_loaded_and_installed_state(self):
        pack = ExamplePack(fail_unload=True)
        manager = PackManager()
        manager.install(pack)
        manager.load("example", "1.0")

        with self.assertRaises(PackLoadError):
            manager.remove("example", "1.0")
        self.assertTrue(manager.get("example", "1.0").loaded)

    def test_manager_remove_unloads_before_unregistering(self):
        pack = ExamplePack()
        manager = PackManager()
        manager.install(pack)
        manager.load("example", "1.0")
        removed = manager.remove("example", "1.0")
        self.assertEqual(removed.identity, ("example", "1.0"))
        self.assertEqual(pack.unload_calls, 1)
        self.assertEqual(manager.list(), ())

    def test_expansion_api_exposes_only_version_aware_pack_management(self):
        api = ExpansionAPI()
        api.install(ExamplePack("alpha", "1"))
        api.install(ExamplePack("alpha", "2"))
        self.assertEqual(api.versions("alpha"), ("1", "2"))
        with self.assertRaises(AmbiguousPackVersionError):
            api.load("alpha")
        loaded = api.load("alpha", "2")
        self.assertTrue(loaded.loaded)
        self.assertEqual(
            [(status.pack_id, status.version, status.loaded) for status in api.list()],
            [("alpha", "1", False), ("alpha", "2", True)],
        )

    def test_living_os_boundary_is_interface_only(self):
        self.assertTrue(inspect.isabstract(LivingOSIntegrationInterface))
        with self.assertRaises(TypeError):
            LivingOSIntegrationInterface()
        self.assertEqual(
            set(LivingOSIntegrationInterface.__abstractmethods__),
            {"connect", "connected", "disconnect"},
        )


if __name__ == "__main__":
    unittest.main()
