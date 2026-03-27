# quiz-gen

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/quiz-gen?color=blue&label=PyPI)](https://pypi.org/project/quiz-gen/)
[![Tests](https://github.com/yauheniya-ai/quiz-gen/actions/workflows/tests.yml/badge.svg)](https://github.com/yauheniya-ai/quiz-gen/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/yauheniya-ai/b7b642418d8dfed95ea2a1fde48de454/raw/coverage.json)](https://github.com/yauheniya-ai/quiz-gen/actions/workflows/tests.yml)
[![GitHub last commit](https://img.shields.io/github/last-commit/yauheniya-ai/quiz-gen)](https://github.com/yauheniya-ai/quiz-gen/commits/main)
[![Downloads](https://pepy.tech/badge/quiz-gen)](https://pepy.tech/project/quiz-gen)


AI-powered quiz generator for regulatory documentation. Extract structured content from complex legal and technical documents to create comprehensive teaching and certification materials.

## Features

- **Multi-Agent Quiz Generation**: Generate, validate, refine, and judge questions using configurable providers/models.
- **EUR-Lex Document Parser**: Parse and structure EU legal documents with full table of contents extraction
- **Human-in-the-Loop**: Integrate human input throughout the workflow.

## Tech Stack

**Backend**
- <img src="https://api.iconify.design/devicon:python.svg" width="16" height="16"> Python — core package language
- <img src="https://api.iconify.design/devicon:fastapi.svg" width="16" height="16"> FastAPI — serves the web UI and REST API from within the package

**AI Providers**
- <img src="https://api.iconify.design/simple-icons:openai.svg" width="16" height="16"> OpenAI
- <img src="https://api.iconify.design/logos:claude-icon.svg" width="16" height="16"> Anthropic
- <img src="https://api.iconify.design/devicon:google.svg" width="16" height="16"> Google (Gemini)
- <img src="https://api.iconify.design/logos:mistral-ai-icon.svg" width="16" height="16"> Mistral
- <img src="https://raw.githubusercontent.com/yauheniya-ai/quiz-gen/main/.github/.images/cohere-color.svg" width="16" height="16"> Cohere

**Web UI**
- <img src="https://api.iconify.design/devicon:react.svg" width="16" height="16"> React — interactive frontend
- <img src="https://api.iconify.design/devicon:vitejs.svg" width="16" height="16"> Vite — fast dev server and production bundler (outputs to `quiz_gen/ui/static`)
- <img src="https://api.iconify.design/devicon:tailwindcss.svg" width="16" height="16"> Tailwind CSS — utility-first styling
- <img src="https://api.iconify.design/devicon:javascript.svg" width="16" height="16"> JavaScript (JSX) — component and API code

**CLI**
- <img src="https://api.iconify.design/devicon:python.svg" width="16" height="16"> argparse — flag-based CLI (`input`, `--output`, `--chunks`, `--toc`, `--print-toc`, `--no-save`, `--verbose`, `--version`)

**Packaging**
- <img src="https://api.iconify.design/devicon:pypi.svg" width="16" height="16"> PyPI — distributed as an installable Python package



## Installation

```bash
pip install quiz-gen
```

## Quick Start

### Multi-Agent Quiz Generation

Quiz generation uses four specialized agents (conceptual, practical, validator, refiner, and judge). Providers are configurable per agent, with supported providers: **Anthropic**, **Cohere**, **Google**, **Mistral**, and **OpenAI**. Any text-generation model name from these providers can be passed directly. The package relies on provider defaults for generation parameters.

<div align="center" style="width: 100%;">
    <img src="https://raw.githubusercontent.com/yauheniya-ai/quiz-gen/main/docs/images/AgentConfig.webp" alt="Multi-Agent Architecture and Configuration" style="width: 100%; height: auto;" />
    <p><em>Multi-Agent Architecture and Configuration</em></p>
</div>

```python
from quiz_gen.agents.workflow import QuizGenerationWorkflow
from quiz_gen.agents.config import AgentConfig

config = AgentConfig(
    conceptual_provider="cohere",
    conceptual_model="command-a-03-2025",
    practical_provider="google",
    practical_model="gemini-3-pro-preview",
    validator_provider="openai",
    validator_model="gpt-5.2-2025-12-11",
    refiner_provider="anthropic",
    refiner_model="claude-sonnet-4-5-20250929",
    judge_provider="mistral",
    judge_model="mistral-large-latest",
)

workflow = QuizGenerationWorkflow(config)
result = workflow.run(chunk)
```

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
├── data/                          # Local data files
│   ├── raw/                       # Source HTML documents
│   ├── processed/                 # Parsed chunks and TOC JSON
│   └── quizzes/                   # Generated quiz output
├── docs/                          # MkDocs documentation source
├── examples/                      # Runnable example scripts
│   ├── eur_lex_html_file.py
│   ├── eur_lex_html_url.py
│   └── quiz_gen_multi_model.py
├── src/
│   └── quiz_gen/                  # Package source
│       ├── agents/                # Multi-agent system
│       │   ├── config.py          # AgentConfig dataclass
│       │   ├── conceptual_generator.py
│       │   ├── practical_generator.py
│       │   ├── validator.py
│       │   ├── refiner.py
│       │   ├── judge.py
│       │   └── workflow.py        # LangGraph orchestration
│       ├── parsers/
│       │   └── html/
│       │       └── eur_lex_parser.py
│       ├── ui/                    # FastAPI + React static bundle
│       │   ├── server.py
│       │   ├── api.py
│       │   └── static/
│       ├── utils/
│       │   └── helpers.py
│       └── cli.py
├── tests/
│   ├── test_agents/
│   ├── test_cli/
│   ├── test_parsers/
│   └── test_utils/
├── pyproject.toml
├── README.md
├── CHANGELOG.md
└── .env
```

## API Reference

### AgentConfig

Dataclass that configures every agent in the multi-agent pipeline. API keys and base URLs are loaded automatically from environment variables when not provided directly.

**Provider / model settings** (per agent – defaults shown):

| Parameter | Default provider | Default model |
|-----------|-----------------|---------------|
| `conceptual_provider` / `conceptual_model` | `openai` | `gpt-4o` |
| `practical_provider` / `practical_model` | `anthropic` | `claude-sonnet-4-20250514` |
| `validator_provider` / `validator_model` | `openai` | `gpt-4o` |
| `refiner_provider` / `refiner_model` | `openai` | `gpt-4o` |
| `judge_provider` / `judge_model` | `anthropic` | `claude-sonnet-4-20250514` |

Supported provider values: `openai`, `anthropic`, `google`, `mistral`, `cohere`.

**Workflow settings**:
- `auto_accept_valid: bool = False` — skip judge when validation already passes
- `save_intermediate_results: bool = True`
- `output_directory: str = "data/quizzes"`
- `min_validation_score: int = 6` — minimum score (out of 10) to pass validation
- `strict_validation: bool = True`
- `max_retries: int = 3`
- `verbose: bool = True`

**Methods**:
- `validate()` — raises `ValueError` if config is invalid
- `save(filepath, verbose=False)` — write config to JSON
- `load(filepath)` *(classmethod)* — load config from JSON
- `print_summary()` — print a human-readable config table

### QuizGenerationWorkflow

LangGraph-based orchestration of the five-agent pipeline.

```python
from quiz_gen.agents.workflow import QuizGenerationWorkflow
from quiz_gen.agents.config import AgentConfig

config = AgentConfig()          # reads API keys from environment
workflow = QuizGenerationWorkflow(config)

# Single chunk
result = workflow.run(chunk)

# Batch
results = workflow.run_batch(chunks, save_output=True, output_dir="data/quizzes")
```

**Methods**:
- `run(chunk, improvement_feedback=None)` → `Dict` — run the full pipeline for one chunk; returns full state including `final_questions`, `judge_decision`, `validation_results`, and `errors`
- `run_batch(chunks, save_output=True, output_dir="data/quizzes")` → `List[Dict]` — run for multiple chunks, optionally saving each result to JSON

### Individual Agents

Agents can be used standalone outside of the workflow:

```python
from quiz_gen.agents.conceptual_generator import ConceptualGenerator
from quiz_gen.agents.practical_generator import PracticalGenerator
from quiz_gen.agents.validator import Validator
from quiz_gen.agents.refiner import Refiner
from quiz_gen.agents.judge import Judge
```

| Class | Key method | Returns |
|-------|------------|---------|
| `ConceptualGenerator` | `generate(chunk, improvement_feedback=None)` | `Dict` question |
| `PracticalGenerator` | `generate(chunk, improvement_feedback=None)` | `Dict` question |
| `Validator` | `validate(qa, chunk)` / `validate_batch(qas, chunk)` | `Dict` / `List[Dict]` |
| `Refiner` | `refine(qa, validation_result, chunk)` / `refine_batch(qas, validation_results, chunk)` | `Dict` / `List[Dict]` |
| `Judge` | `judge(conceptual_qa, practical_qa, chunk)` | `Dict` with `decision` and `reasoning` |

---

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
- Support automated document analysis workflows
- Build searchable knowledge bases from legal texts

### Education and Training

- Generate study materials from regulatory documents
- Create structured learning paths for certification programs
- Extract key concepts for examination preparation

## Supported Document Types

Currently supports:

- **EUR-Lex HTML Documents**: European Union regulations, directives, decisions

### Document Format Requirements

- Documents must use EUR-Lex HTML format
- Must contain `eli-subdivision` elements for proper structure identification
- Supports multi-level hierarchies with chapters, sections, and articles

## TODOs

- [ ] Integrate human feedback
- [ ] Save results by project in a local database
- [ ] Support for additional document formats (PDF, DOCX, PPTX)
- [ ] Multi-language support for UI
- [ ] Light/Dark scheme for UI

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
2. All tests pass: `pytest --cov=src --cov-report=term-missing`
3. New features include appropriate tests
4. Documentation is updated
