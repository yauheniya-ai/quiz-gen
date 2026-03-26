# quiz-gen

AI-powered toolkit for parsing EUR-Lex regulatory documents and generating structured quiz content using a configurable multi-agent pipeline.

## Overview

quiz-gen transforms complex EU legal documents into JSON-structured content and generates high-quality multiple-choice questions via five coordinated AI agents. It ships as a self-contained Python package with a built-in web UI, a CLI, and a fully programmable API.

### Capabilities

- **EUR-Lex document parser**: Extracts hierarchical structure, table of contents, and cleaned text from EU regulations, directives, and decisions
- **Multi-agent quiz generation**: Five specialized agents (Conceptual Generator, Practical Generator, Validator, Refiner, Judge) orchestrated by a LangGraph workflow
- **Configurable providers**: Each agent independently uses OpenAI, Anthropic, Google, Mistral, or Cohere
- **Web UI**: Built-in browser interface for document parsing and quiz generation, served directly from the package via FastAPI
- **CLI**: Flag-based command-line interface for document parsing and launching the web UI
- **Python API**: Fully programmable access to the parser, agents, and workflow

## Quick start

### Parse a document

```python
from quiz_gen import EURLexParser

url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401689"
parser = EURLexParser(url=url)
chunks, toc = parser.parse()

print(f"Title: {toc['title']}")
print(f"Total chunks: {len(chunks)}")

parser.save_chunks("data/processed/chunks.json")
parser.save_toc("data/processed/toc.json")
```

### Generate quiz questions

```python
from quiz_gen.agents.workflow import QuizGenerationWorkflow
from quiz_gen.agents.config import AgentConfig

config = AgentConfig()  # reads API keys from environment variables
workflow = QuizGenerationWorkflow(config)

result = workflow.run(chunks[50])  # pass any RegulationChunk dict

print(f"Judge decision: {result['judge_decision']}")
for q in result["final_questions"]:
    print(f"\n[{q['focus']}] {q['question']}")
```

### Launch the web UI

```bash
quiz-gen --ui
```

Opens `http://localhost:8000` in the browser automatically. Custom port:

```bash
quiz-gen --ui --port 9000
```

## CLI reference

```bash
# Parse from URL, save to data/processed/
quiz-gen https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139

# Parse a local file and print the table of contents
quiz-gen data/raw/regulation.html --print-toc --no-save

# Launch the web UI on a custom port without auto-opening the browser
quiz-gen --ui --port 9000 --no-browser
```

See [CLI reference](cli.md) for the full option set.

## Document structure

EUR-Lex documents are extracted into a hierarchical structure:

```
Document
├── Title
├── Preamble
│   ├── Citation (combined into one chunk)
│   └── Recitals (one chunk per recital)
├── Enacting Terms
│   └── Chapters
│       ├── Articles
│       └── Sections (when present)
│           └── Articles
├── Concluding Formulas
└── Annexes
```

Each content unit becomes a `RegulationChunk` with `section_type`, `number`, `title`, `content`, `hierarchy_path`, and `metadata` fields.

## Supported document types

The parser handles EUR-Lex HTML documents:

- EU Regulations
- EU Directives
- EU Decisions
- Annexes containing tables

Documents must use the EUR-Lex HTML format with `eli-subdivision` elements for structure identification.

## Installation

```bash
pip install quiz-gen
```

Requires Python 3.10 or higher.

## Next steps

- [Getting Started](getting-started.md) — installation and first examples
- [Parsers](parsers.md) — EUR-Lex parser reference
- [Agents](agents.md) — multi-agent quiz generation architecture
- [CLI](cli.md) — command-line interface reference
- [API Reference](api.md) — complete class and method documentation
- [Examples](examples.md) — working code examples

## Support

- Documentation: [https://quiz-gen.readthedocs.io](https://quiz-gen.readthedocs.io)
- Issues: [GitHub Issue Tracker](https://github.com/yauheniya-ai/quiz-gen/issues)
- PyPI: [https://pypi.org/project/quiz-gen](https://pypi.org/project/quiz-gen)

## License

quiz-gen is released under the MIT License. See [LICENSE](https://github.com/yauheniya-ai/quiz-gen/blob/main/LICENSE) for details.
