# Comprehensive tests for EURLexParser

import os
from src.quiz_gen.parsers.html.eur_lex_parser import EURLexParser, SectionType

TEST_HTML_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../data/raw/2024_1689_Artificial Intelligence_Act.html",
)


def get_parser():
    with open(TEST_HTML_PATH, encoding="utf-8") as f:
        html_content = f.read()
    return EURLexParser(html_content=html_content)


def test_parse_returns_chunks_and_toc():
    parser = get_parser()
    chunks, toc = parser.parse()
    assert isinstance(chunks, list)
    assert isinstance(toc, dict)
    assert len(chunks) > 0
    assert "sections" in toc


def test_title_chunk():
    parser = get_parser()
    chunks, toc = parser.parse()
    title_chunks = [c for c in chunks if c.section_type == SectionType.TITLE]
    assert len(title_chunks) == 1
    chunk = title_chunks[0]
    assert "REGULATION (EU) 2024/1689" in chunk.title
    assert chunk.content.startswith("REGULATION (EU) 2024/1689")


def test_preamble_chunk():
    parser = get_parser()
    chunks, _ = parser.parse()
    preamble_chunks = [c for c in chunks if c.section_type == SectionType.PREAMBLE]
    assert len(preamble_chunks) == 1
    assert "EUROPEAN PARLIAMENT" in preamble_chunks[0].content


def test_citation_chunk():
    parser = get_parser()
    chunks, _ = parser.parse()
    citation_chunks = [c for c in chunks if c.section_type == SectionType.CITATION]
    assert len(citation_chunks) == 1
    assert (
        "Treaty on the Functioning of the European Union" in citation_chunks[0].content
    )


def test_recital_chunks():
    parser = get_parser()
    chunks, _ = parser.parse()
    recitals = [c for c in chunks if c.section_type == SectionType.RECITAL]
    assert len(recitals) > 50
    for r in recitals[:3]:
        assert r.title.startswith("Recital")
        assert r.content


def test_article_chunks():
    parser = get_parser()
    chunks, _ = parser.parse()
    articles = [c for c in chunks if c.section_type == SectionType.ARTICLE]
    assert len(articles) > 10
    for a in articles[:3]:
        assert a.title.startswith("Article")
        assert a.content


def test_annex_and_appendix_chunks():
    parser = get_parser()
    chunks, _ = parser.parse()
    annexes = [c for c in chunks if c.section_type == SectionType.ANNEX]
    assert len(annexes) >= 1
    for a in annexes:
        assert "ANNEX" in a.title or "Annex" in a.title
        assert a.content


def test_toc_structure():
    parser = get_parser()
    _, toc = parser.parse()
    assert "sections" in toc
    section_titles = [s["title"].lower() for s in toc["sections"] if "title" in s]
    assert any("preamble" in t for t in section_titles)
    assert any("enacting" in t for t in section_titles)


def test_chunk_hierarchy_paths():
    parser = get_parser()
    chunks, _ = parser.parse()
    for c in chunks:
        assert isinstance(c.hierarchy_path, list)
        assert c.hierarchy_path


def test_chunk_to_dict():
    parser = get_parser()
    chunks, _ = parser.parse()
    d = chunks[0].to_dict()
    assert isinstance(d, dict)
    assert "section_type" in d
    assert "content" in d
