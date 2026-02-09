import importlib
import sys
from unittest import mock

import pytest


def test_version_fallback(monkeypatch):
    module_name = "quiz_gen.__version__"
    if module_name in sys.modules:
        del sys.modules[module_name]
    with mock.patch("importlib.metadata.version", side_effect=Exception("fail")):
        with pytest.raises(Exception):
            importlib.import_module(module_name)
