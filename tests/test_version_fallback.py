import sys
from unittest import mock

import importlib


def test_version_fallback(monkeypatch):
    # Patch importlib.metadata.version to raise an exception
    module_name = "quiz_gen.__version__"
    # Remove from sys.modules to force reload
    if module_name in sys.modules:
        del sys.modules[module_name]
    with mock.patch("importlib.metadata.version", side_effect=Exception("fail")):
        version_mod = importlib.import_module(module_name)
        assert version_mod.__version__ == "0.2.8"
