# quiz-gen

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/quiz-gen?color=blue&label=PyPI)](https://pypi.org/project/quiz-gen/)
[![Tests](https://github.com/yauheniya-ai/quiz-gen/actions/workflows/tests.yml/badge.svg)](https://github.com/yauheniya-ai/quiz-gen/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/yauheniya-ai/b7b642418d8dfed95ea2a1fde48de454/raw/coverage.json)](https://github.com/yauheniya-ai/quiz-gen/actions/workflows/tests.yml)
[![GitHub last commit](https://img.shields.io/github/last-commit/yauheniya-ai/quiz-gen)](https://github.com/yauheniya-ai/quiz-gen/commits/main)
[![Downloads](https://pepy.tech/badge/quiz-gen)](https://pepy.tech/project/quiz-gen)


AI-powered quiz generator for regulatory, certification, and educational documentation. Extract structured content from complex legal and technical documents to create comprehensive learning materials.

## Features

- **Multi-Agent Quiz Generation**: Generate, validate, and judge questions using configurable providers/models
- **EUR-Lex Document Parser**: Parse and structure EU legal documents with full table of contents extraction
- **Hierarchical Document Analysis**: Identify structure including chapters, sections, articles, recitals, annexes, and appendices
- **Intelligent Chunking**: Extract meaningful content chunks for articles, recitals, annexes, and appendices

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

#### Working with Chunks

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

#### Displaying Table of Contents

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

### Multi-Agent Quiz Generation

Quiz generation uses four specialized agents (conceptual, practical, validator, judge). Providers are configurable per agent, with supported providers: **Anthropic**, **Google**, **Mistral**, and **OpenAI**. Any text-generation model name from these providers can be passed directly. The package relies on provider defaults for generation parameters.

<div align="center" style="width: 100%;">
    <img src="docs/images/Screenshot_AgentConfig.png" alt="Multi-Agent Architecture and Configuration" style="width: 100%; height: auto;" />
    <p><em>Multi-Agent Architecture and Configuration</em></p>
</div>

```python
from quiz_gen.agents.workflow import QuizGenerationWorkflow
from quiz_gen.agents.config import AgentConfig

config = AgentConfig(
    conceptual_provider="openai",
    practical_provider="anthropic",
    validator_provider="google",
    judge_provider="mistral",
    conceptual_model="gpt-4o",
    practical_model="claude-sonnet-4-20250514",
    validator_model="gemini-2.5-flash",
    judge_model="mistral-large-latest",
)

workflow = QuizGenerationWorkflow(config)
result = workflow.run(chunk)
```

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

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/yauheniya-ai/quiz-gen.git
cd quiz-gen

# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest --cov=src --cov-report=term-missing

# Run linting
ruff check .
black .
```

### Project Structure
```
quiz-gen/
├── data/             
│   ├── raw/
│   ├── processed/
│   └── quizzes/
├── src/
│   └── quiz_gen/          # Module code here
│       ├── agents/
│       ├── parsers/
│       └── ...
├── examples/              # Example scripts
│   ├── eur_lex_html_url.py
│   └── quiz_gen_multi_model.py
├── pyproject.toml
└── .env
```

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

## Roadmap

Future enhancements planned:

- Support for additional document formats (PDF, DOCX, PPTX)
- Multi-language support
- Integration with learning management systems

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Citation

If you use this software in academic work, please cite:

```
Varabyova, Y. (2026). Quiz Gen AI: AI-powered quiz generator for professional certification.
GitHub repository: https://github.com/yauheniya-ai/quiz-gen
```

## Support

- Documentation: https://quiz-gen.readthedocs.io
- Issue Tracker: https://github.com/yauheniya-ai/quiz-gen/issues

### Contributing

Contributions are welcome! Please ensure:

1. Code follows PEP 8 style guidelines
2. All tests pass
3. New features include appropriate tests
4. Documentation is updated
