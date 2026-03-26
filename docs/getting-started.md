# Getting Started

This guide covers installation, parsing your first document, generating quiz questions, and launching the web UI.

## Installation

```bash
pip install quiz-gen
```

Verify the installation:

```bash
quiz-gen --version
```

### Development installation

```bash
git clone https://github.com/yauheniya-ai/quiz-gen.git
cd quiz-gen
pip install -e ".[dev]"
```

## Parsing a document

### Using the CLI

Parse a EUR-Lex regulation directly from its URL:

```bash
quiz-gen https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139
```

This downloads the document, parses it, and saves two files to `data/processed/`:

- `32018R1139_chunks.json` — all content units with metadata
- `32018R1139_toc.json` — hierarchical table of contents

Parse a local HTML file:

```bash
quiz-gen data/raw/regulation.html
```

Specify an output directory and print the table of contents:

```bash
quiz-gen data/raw/regulation.html --output data/processed --print-toc
```

### Using Python

```python
from quiz_gen import EURLexParser

# Parse from URL
url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139"
parser = EURLexParser(url=url)
chunks, toc = parser.parse()

print(f"Title: {toc['title']}")
print(f"Total chunks: {len(chunks)}")

# Save results
parser.save_chunks("data/processed/chunks.json")
parser.save_toc("data/processed/toc.json")
```

### Parsing a local file

```python
from quiz_gen import EURLexParser

with open("data/raw/regulation.html", "r", encoding="utf-8") as f:
    html_content = f.read()

parser = EURLexParser(html_content=html_content)
chunks, toc = parser.parse()
```

## Understanding the output

### Chunks

Each document is split into `RegulationChunk` objects representing logical units:

```json
{
  "section_type": "article",
  "number": "1",
  "title": "Article 1 - Subject matter and objectives",
  "content": "1. The principal objective of this Regulation...",
  "hierarchy_path": ["Enacting Terms", "CHAPTER I - PRINCIPLES", "Article 1..."],
  "metadata": {"id": "art_1", "subtitle": "Subject matter and objectives"}
}
```

| `section_type` value | Description |
|---------------------|-------------|
| `title` | Document title |
| `citation` | Combined citations block |
| `recital` | Individual recital |
| `article` | Article (main content unit) |
| `annex` | Annex |
| `concluding_formulas` | Signatures and adoption info |

### Table of contents

A dictionary with a `title` key and a `sections` list describing the full document hierarchy, including chapter, section, and article nesting.

## Filtering chunks

```python
from quiz_gen import EURLexParser, SectionType

parser = EURLexParser(url=url)
chunks, toc = parser.parse()

articles = [c for c in chunks if c.section_type == SectionType.ARTICLE]
recitals = [c for c in chunks if c.section_type == SectionType.RECITAL]
print(f"Articles: {len(articles)}, Recitals: {len(recitals)}")

# Find a specific article by number
article_5 = next(
    c for c in chunks
    if c.section_type == SectionType.ARTICLE and c.number == "5"
)
print(article_5.content[:200])
```

## Generating quiz questions

Quiz generation requires at least one AI provider API key. Set the relevant environment variable or create a `.env` file in the project root:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Basic usage

```python
from quiz_gen import EURLexParser
from quiz_gen.agents.workflow import QuizGenerationWorkflow
from quiz_gen.agents.config import AgentConfig

# Parse a document
parser = EURLexParser(url="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139")
chunks, _ = parser.parse()

# Configure and run the workflow (reads keys from environment)
config = AgentConfig()
workflow = QuizGenerationWorkflow(config)

# Generate questions for one article
result = workflow.run(chunks[50].to_dict())

print(f"Judge decision: {result['judge_decision']}")
for q in result["final_questions"]:
    print(f"\n[{q['focus']}] {q['question']}")
    for letter, text in q["options"].items():
        print(f"  {letter}. {text}")
    print(f"  Correct: {q['correct_answer']}")
```

### Configuring providers

Providers and models are independently configurable per agent:

```python
config = AgentConfig(
    conceptual_provider="openai",
    conceptual_model="gpt-4o",
    practical_provider="anthropic",
    practical_model="claude-sonnet-4-20250514",
    validator_provider="openai",
    validator_model="gpt-4o",
    refiner_provider="openai",
    refiner_model="gpt-4o",
    judge_provider="anthropic",
    judge_model="claude-sonnet-4-20250514",
)
```

Supported provider values: `openai`, `anthropic`, `google`, `mistral`, `cohere`.

See [Agents](agents.md) for the full configuration reference.

## Using the web UI

The web UI is built into the package. Launch it with:

```bash
quiz-gen --ui
```

The browser opens automatically at `http://localhost:8000`. Additional options:

```bash
# Custom port
quiz-gen --ui --port 9000

# Skip automatic browser opening
quiz-gen --ui --no-browser

# Bind to localhost only
quiz-gen --ui --host 127.0.0.1

# Set server log level
quiz-gen --ui --log-level info
```

The UI supports document parsing by URL or file upload, TOC navigation, chunk preview, and quiz generation with configurable AI providers.

## Common patterns

### Batch processing multiple documents

```python
from pathlib import Path
from quiz_gen import EURLexParser

for path in Path("data/raw").glob("*.html"):
    with open(path, encoding="utf-8") as f:
        html = f.read()
    parser = EURLexParser(html_content=html)
    chunks, toc = parser.parse()
    parser.save_chunks(f"data/processed/{path.stem}_chunks.json")
    parser.save_toc(f"data/processed/{path.stem}_toc.json")
    print(f"Processed {path.name}: {len(chunks)} chunks")
```

### Preview TOC without saving

```bash
quiz-gen --print-toc --no-save regulation.html
```

Or in Python:

```python
parser.print_toc()
```

### Search chunk content

```python
# Find all articles mentioning "safety"
safety_articles = [
    c for c in chunks
    if c.section_type == SectionType.ARTICLE
    and "safety" in c.content.lower()
]

for article in safety_articles:
    print(f"Article {article.number}: {article.title}")
```

## Next steps

- [Parsers](parsers.md) — full EUR-Lex parser reference and output structure
- [Agents](agents.md) — multi-agent pipeline architecture and configuration
- [CLI](cli.md) — complete CLI reference
- [API Reference](api.md) — full class and method documentation
- [Examples](examples.md) — complete working examples