import inspect
import unittest

import expansion
from expansion import ExpansionAPI


class V10PublicAPITests(unittest.TestCase):
    def test_primary_facade_operations_are_frozen(self):
        expected = {
            "install",
            "remove",
            "load",
            "unload",
            "start",
            "stop",
            "session",
            "sessions",
            "get",
            "list",
            "versions",
        }
        public_methods = {
            name
            for name, value in inspect.getmembers(ExpansionAPI, inspect.isfunction)
            if not name.startswith("_")
        }
        self.assertEqual(public_methods, expected)

    def test_interface_version_and_stable_status_types_are_exported(self):
        self.assertEqual(expansion.EXPANSION_INTERFACE_VERSION, "0.7")
        self.assertIn("PackStatus", expansion.__all__)
        self.assertIn("PackSessionStatus", expansion.__all__)
        self.assertIn("PackExecutionError", expansion.__all__)
        self.assertNotIn("PackStateCoordinator", expansion.__all__)


if __name__ == "__main__":
    unittest.main()
