"""Document parsers for various formats."""

from quiz_gen.parsers.html.eur_lex_parser import (
    EURLexParser,
    RegulationChunk,
    SectionType,
)

__all__ = [
    "EURLexParser",
    "RegulationChunk",
    "SectionType",
]
