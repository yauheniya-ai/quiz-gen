"""Version information for quiz-gen package."""

from importlib.metadata import version, metadata

__version__ = version("quiz-gen")

try:
    _metadata = metadata("quiz-gen")
    __author__ = _metadata.get("Author", "Yauheniya Varabyova")
except Exception:
    __author__ = "Yauheniya Varabyova"
