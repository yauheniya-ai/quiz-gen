"""Quiz Gen AI - AI-powered quiz generator for regulatory and educational documentation."""

try:
    from quiz_gen.__version__ import __version__, __author__
except ImportError:
    __version__ = "0.1.0.dev"
    __author__ = "Yauheniya Varabyova"

from quiz_gen.parsers.html.eu_lex_parser import (
    EURLexParser,
    RegulationChunk,
    SectionType,
)

__all__ = [
    "__version__",
    "__author__",
    "EURLexParser",
    "RegulationChunk",
    "SectionType",
]
