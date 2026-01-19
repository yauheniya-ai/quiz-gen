# quiz-gen

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/quiz-gen?color=blue&label=PyPI)](https://pypi.org/project/quiz-gen/)
[![GitHub last commit](https://img.shields.io/github/last-commit/yauheniya-ai/quiz-gen)](https://github.com/yauheniya-ai/quiz-gen/commits/main)
[![Downloads](https://pepy.tech/badge/quiz-gen)](https://pepy.tech/project/quiz-gen)


AI-powered quiz generator for regulatory, certification, and educational documentation. Extract structured content from complex legal and technical documents to create comprehensive learning materials.

## Features

- **EUR-Lex Document Parser**: Parse and structure European Union legal documents with full table of contents extraction
- **Hierarchical Document Analysis**: Automatically identify document structure including chapters, sections, articles, and recitals
- **Intelligent Chunking**: Extract meaningful content chunks at appropriate granularity levels (articles and recitals)
- **Table of Contents Generation**: Build complete document navigation structure with 3-level hierarchy
- **Regulatory Document Support**: Specialized parsing for aviation regulations, directives, and other technical documentation

## Installation

```bash
pip install quiz-gen
```

## Quick Start

### Parsing EUR-Lex Documents

```python
from quiz_gen import EURLexParser

# Parse a regulation document
url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401689"
parser = EURLexParser(url=url)
chunks, toc = parser.parse()

# Access structured content
print(f"Extracted {len(chunks)} content chunks")
print(f"Document has {len(toc['sections'])} major sections")

# Save results
parser.save_chunks('output_chunks.json')
parser.save_toc('output_toc.json')
```

### Document Structure

The parser extracts documents into a multi-level hierarchy:

**Level 1**: Major Sections
- Preamble
- Enacting Terms

**Level 2/3**: Structural Divisions
- Chapters
- Sections

**Level 1/2/3/4**: Content Elements
- Title
- Citation
- Recitals
- Articles
- Concluding formulas
- Annex
- Appendix

### Working with Chunks

```python
# Iterate through extracted chunks
for chunk in chunks:
    print(f"{chunk.title}")
    print(f"Type: {chunk.section_type.value}")
    print(f"Number: {chunk.number}")
    print(f"Content: {chunk.content[:200]}...")
    print(f"Hierarchy: {' > '.join(chunk.hierarchy_path)}")
    print()
```

### Displaying Table of Contents

```python
# Print formatted TOC
parser.print_toc()

# Output:
# PREAMBLE
#   Citation 
#   Recital 1
#   Recital 2
#   ...
# 
# ENACTING TERMS
#   CHAPTER I - PRINCIPLES
#     Article 1 - Subject matter and objectives
#     Article 2 - Scope
```

## Use Cases

### Compliance and Legal

- Analyze regulatory requirements systematically
- Track changes across document versions
- Build searchable knowledge bases from legal texts

### Documentation Processing

- Convert unstructured documents into structured data
- Build citation networks and cross-references
- Support automated document analysis workflows

### Education and Training

- Generate study materials from regulatory documents
- Create structured learning paths for certification programs
- Extract key concepts for examination preparation

## Supported Document Types

Currently supports:

- **EUR-Lex HTML Documents**: European Union regulations, directives, decisions
- **Legislative Acts**: Structured legal documents with formal hierarchies

### Document Format Requirements

- Documents must use EUR-Lex HTML format
- Must contain `eli-subdivision` elements for proper structure identification
- Supports multi-level hierarchies with chapters, sections, and articles

## Advanced Usage

### Custom Parsing Workflows

```python
from quiz_gen import EURLexParser

parser = EURLexParser(url=document_url)

# Parse specific sections
parser._parse_preamble()  # Extract citations and recitals
parser._parse_enacting_terms()  # Extract chapters and articles
parser._parse_annexes()  # Extract annexes

# Access intermediate results
toc = parser.toc  # Full table of contents
chunks = parser.chunks  # Content chunks only
```

### Filtering Chunks by Type

```python
from quiz_gen import SectionType

# Get only recitals
recitals = [c for c in chunks if c.section_type == SectionType.RECITAL]

# Get only articles
articles = [c for c in chunks if c.section_type == SectionType.ARTICLE]

# Filter by chapter
chapter_1_articles = [
    c for c in articles 
    if 'CHAPTER I' in ' > '.join(c.hierarchy_path)
]
```

### Accessing Metadata

```python
for chunk in chunks:
    # Access structured metadata
    print(chunk.metadata)  # {'id': 'art_1', 'subtitle': '...'}
    
    # Navigate hierarchy
    print(chunk.hierarchy_path)  # ['CHAPTER I - PRINCIPLES', 'Article 1']
    
    # Identify parent sections
    print(chunk.parent_section)
```

## Project Structure

```
quiz-gen/
├── src/
│   └── quiz_gen/
│       ├── parsers/
│       │   └── html/
│       │       └── eu_lex_parser.py
│       ├── models/
│       │   ├── chunk.py
│       │   ├── document.py
│       │   └── quiz.py
│       └── utils/
├── examples/
│   └── eu_lex_toc_chunks.py
├── tests/
├── data/
│   ├── processed/
│   └── raw/
└── docs/
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/yauheniya-ai/quiz-gen.git
cd quiz-gen

# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
black .
```


### Contributing

Contributions are welcome! Please ensure:

1. Code follows PEP 8 style guidelines
2. All tests pass
3. New features include appropriate tests
4. Documentation is updated

## API Reference

### EURLexParser

Main parser class for EUR-Lex documents.

**Methods**:
- `parse()` -> `tuple[List[RegulationChunk], Dict]`: Parse document and return chunks and TOC
- `fetch()` -> `str`: Fetch HTML content from URL
- `save_chunks(filepath: str)`: Save chunks to JSON file
- `save_toc(filepath: str)`: Save table of contents to JSON file
- `print_toc()`: Display formatted table of contents

### RegulationChunk

Represents a parsed content chunk (article or recital).

**Attributes**:
- `section_type`: Type of section (ARTICLE, RECITAL, etc.)
- `number`: Section number (e.g., "1", "42")
- `title`: Full title including subtitle
- `content`: Text content
- `hierarchy_path`: List of parent sections
- `metadata`: Additional structured data

### SectionType

Enumeration of document section types.

**Values**:
- `PREAMBLE`: Preamble section
- `ENACTING_TERMS`: Main regulatory content
- `CITATION`: Citation in preamble
- `RECITAL`: Recital in preamble
- `CHAPTER`: Chapter division
- `SECTION`: Section within chapter
- `ARTICLE`: Article (main content unit)
- `ANNEX`: Annex section

## Roadmap

Future enhancements planned:

- AI-powered quiz generation from extracted content
- Support for additional document formats (PDF, DOCX, PPTX)
- Multi-language support
- Question validation and quality metrics
- Integration with learning management systems
- Version comparison and diff analysis

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Citation

If you use this software in academic work, please cite:

```
Varabyova, Y. (2026). Quiz Gen AI: AI-powered quiz generator for regulatory documentation.
GitHub repository: https://github.com/yauheniya-ai/quiz-gen
```

## Support

- Documentation: https://quiz-gen.readthedocs.io
- Issue Tracker: https://github.com/yauheniya-ai/quiz-gen/issues

## Acknowledgments

Built with:
- BeautifulSoup4 for HTML parsing
- lxml for XML processing
- EUR-Lex for providing structured legal documents

## Changelog

### Version 0.1.0 (2026-01-17)

Initial release:
- EUR-Lex document parser
- Hierarchical document structure extraction
- Table of contents generation
- JSON export for chunks and TOC

### Version 0.1.1 (2026-01-18)

Parser enhancements:
- Added regulation title extraction and chunking
- Support for flexible 3-4 level hierarchy with sections within chapters
- Complete annexes extraction including table-based content
- Combined citations into single chunk matching EU-Lex structure
- Added concluding formulas parsing

### Version 0.1.2 (2026-01-18)

Text formatting and tooling:
- Implemented smart text cleaning for proper list formatting (removes extra newlines after list markers)
- Fixed numbered paragraph spacing
- Added professional command-line interface (CLI)
- Created comprehensive documentation with MkDocs and Material theme

### Version 0.1.3 (2026-01-19)

Parser robustness improvements:
- Fixed parsing of articles directly under enacting terms (without chapter hierarchy)
- Enhanced article content extraction to handle table-based list items (e.g., (a), (b), (c) in table cells)
- Added proper appendix detection and parsing (distinguishes appendices from annexes)
- Improved title extraction for multi-paragraph appendix titles

### Version 0.1.4 (2026-01-19)

Annex parsing improvements:
- Added intelligent detection and parsing of parts within annexes (PART 1, PART 2, etc.)
- Improved part titles to include annex identifier (e.g., "ANNEX 1 - PART 1" instead of "ANNEX - PART 1")
- Removed arbitrary content truncation in annexes and appendices - all content now preserved in full
- Enhanced content collection for parts with proper boundary detection between sections

### Version 0.1.5 (2026-01-19)

Bug fixes:
- Fixed annex TOC title to display with identifier (e.g., "ANNEX 1" instead of "ANNEX")
- Fixed empty content in annex parts by switching from sibling navigation to descendants iteration

### Version 0.1.6 (2026-01-19)

Content extraction improvements:
- Enhanced part content extraction to include all paragraph types (titles, headings, body text)
- Fixed missing section titles and numbered headings in annex parts
- Lowered text length threshold to capture short titles (5 chars instead of 10)
- Added smart filtering to skip only PART headers while collecting all other content

### Version 0.1.7 (2026-01-19)

List structure preservation:
- Added detection and proper handling of list-item tables (numbered and lettered items)
- Fixed extraction of nested list structures by processing direct content only
- Preserved list markers like (8), (a), (b), (—) with their corresponding text
- Separated handling of list tables vs data tables for appropriate formatting