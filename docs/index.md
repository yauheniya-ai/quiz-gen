# Quiz-Gen Documentation

Welcome to Quiz-Gen, an AI-powered toolkit for parsing and extracting structured content from regulatory, certification, and educational documentation.

## Overview

Quiz-Gen specializes in transforming complex legal and technical documents into structured, machine-readable formats. It's designed for developers, researchers, and organizations working with regulatory documentation who need to extract, analyze, and process content at scale.

### Key Features

- **🔍 Intelligent Document Parsing**: Extract hierarchical structure from EUR-Lex and regulatory documents
- **📊 Structured Output**: Generate clean JSON with chunks and table of contents
- **🎯 Granular Content Extraction**: Chunk content at article and recital level with full hierarchy
- **🌐 Flexible Input**: Support for both URLs and local HTML files
- **⚡ CLI & Python API**: Use via command-line or programmatically in your code
- **🧹 Smart Text Cleaning**: Preserve document structure while removing formatting artifacts
- **📝 Complete Metadata**: Track IDs, hierarchy paths, and cross-references

## What Can You Build?

### Education & Training
- Generate quiz questions from regulatory content
- Create structured study materials for certification exams
- Build interactive learning platforms

### Compliance & Legal
- Analyze regulatory requirements systematically
- Track changes across document versions
- Build searchable knowledge bases

### Research & Analysis
- Extract data for legal research
- Perform comparative analysis of regulations
- Build citation networks

### Automation
- Automate document processing workflows
- Generate reports from regulatory data
- Build AI-powered legal assistants

## Quick Example

```python
from quiz_gen.parsers.html.eu_lex_parser import EURLexParser

# Parse a regulation
url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139"
parser = EURLexParser(url=url)
chunks, toc = parser.parse()

# Access structured content
print(f"Document: {toc['title']}")
print(f"Total chunks: {len(chunks)}")

# Filter by type
articles = [c for c in chunks if c.section_type.value == 'article']
recitals = [c for c in chunks if c.section_type.value == 'recital']

print(f"Articles: {len(articles)}, Recitals: {len(recitals)}")
```

## Command-Line Interface

```bash
# Parse from URL
quiz-gen https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139

# Parse local file
quiz-gen data/documents/regulation.html

# Specify output directory
quiz-gen --output data/processed regulation.html

# Print table of contents
quiz-gen --print-toc regulation.html
```

## Supported Document Types

Currently supports EUR-Lex HTML documents:

- ✅ EU Regulations
- ✅ EU Directives
- ✅ EU Decisions
- ✅ Annexes with tables

## Architecture

### Document Structure

```
Document
├── Title (Level 0)
├── Preamble (Level 1)
│   ├── Citation
│   └── Recitals (Level 2)
├── Enacting Terms (Level 1)
│   └── Chapters (Level 2)
│       ├── Articles (Level 3)
│       └── Sections (Level 3, optional)
│           └── Articles (Level 4)
├── Concluding Formulas (Level 1)
└── Annexes (Level 1)
```

### Content Chunks

Each chunk contains:
- **Type**: title, citation, recital, article, annex, concluding_formulas
- **Number**: Sequential identifier (when applicable)
- **Title**: Full title including subtitle
- **Content**: Cleaned text content
- **Hierarchy Path**: List of parent sections
- **Metadata**: IDs, subtitles, and references

### Table of Contents

Hierarchical JSON structure with:
- Document title
- Nested sections and subsections
- Links to all content elements
- Type identifiers for each node

## Installation

```bash
pip install quiz-gen
```

### Requirements

- Python 3.10 or higher
- Dependencies: beautifulsoup4, lxml, requests

## Next Steps

- **[Getting Started](getting-started.md)** - Installation and first steps
- **[Parsers](parsers.md)** - Detailed parser documentation
- **[API Reference](api.md)** - Complete API documentation
- **[Examples](examples.md)** - Practical usage examples

## Project Status

Quiz-Gen is actively developed and maintained. Current focus:

- ✅ EUR-Lex HTML parser (complete)
- 🚧 AI-powered quiz generation (in development)
- 📋 PDF document support (planned)
- 📋 Multi-language support (planned)

## Contributing

We welcome contributions! Whether you're fixing bugs, adding features, or improving documentation:

1. Check existing issues or create a new one
2. Fork the repository
3. Create a feature branch
4. Submit a pull request

See our [GitHub repository](https://github.com/yauheniya-ai/quiz-gen) for more details.

## Support

- **Documentation**: [https://quiz-gen.readthedocs.io](https://quiz-gen.readthedocs.io)
- **Issues**: [GitHub Issue Tracker](https://github.com/yauheniya-ai/quiz-gen/issues)
- **PyPI**: [https://pypi.org/project/quiz-gen](https://pypi.org/project/quiz-gen)

## License

Quiz-Gen is released under the MIT License. See [LICENSE](https://github.com/yauheniya-ai/quiz-gen/blob/main/LICENSE) for details.

---

**Ready to get started?** Check out the [Getting Started guide](getting-started.md) →
