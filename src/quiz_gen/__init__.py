"""Quiz Gen AI - AI-powered quiz generator for regulatory and educational documentation."""

from quiz_gen.__version__ import __version__
from quiz_gen.parsers.html.eur_lex_parser import (
    EURLexParser,
    RegulationChunk,
    SectionType,
)

__all__ = [
    "__version__",
    "EURLexParser",
    "RegulationChunk",
    "SectionType",
]
