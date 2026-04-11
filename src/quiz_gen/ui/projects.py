"""Backward-compatibility shim — import from quiz_gen.storage instead."""
from ..storage.projects import *  # noqa: F401, F403
from ..storage.projects import router, save_document, save_quiz, save_debug  # noqa: F401
