"""Version information for quiz-gen package."""

from importlib.metadata import version, metadata

__version__ = version("quiz-gen")

try:
    _metadata = metadata("quiz-gen")
    __author__ = _metadata.get("Author", "Yauheniya Varabyova")
    __email__ = _metadata.get("Author-email", "yauheniya.ai@gmail.com")
except Exception:
    __author__ = "Yauheniya Varabyova"
    __email__ = "yauheniya.ai@gmail.com"
