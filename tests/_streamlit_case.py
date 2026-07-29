import os
import tempfile
import unittest
from pathlib import Path


class IsolatedWorldStateTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._world_state_directory = tempfile.TemporaryDirectory()
        self._previous_world_state_path = os.environ.get("ULE_DATA_PATH")
        os.environ["ULE_DATA_PATH"] = str(
            Path(self._world_state_directory.name) / "world_state.json"
        )

    def tearDown(self):
        if self._previous_world_state_path is None:
            os.environ.pop("ULE_DATA_PATH", None)
        else:
            os.environ["ULE_DATA_PATH"] = self._previous_world_state_path
        self._world_state_directory.cleanup()
        super().tearDown()
