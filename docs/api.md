# API Reference

Complete reference for all public classes and methods in quiz-gen.

## Parser

### EURLexParser

Main parser class for EUR-Lex HTML documents.

```python
from quiz_gen import EURLexParser
```

#### Constructor

```python
EURLexParser(url: str = None, html_content: str = None)
```

One of `url` or `html_content` must be provided.

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | URL of a EUR-Lex document to fetch |
| `html_content` | `str` | Raw HTML string to parse directly |

```python
# From URL
parser = EURLexParser(url="https://eur-lex.europa.eu/.../CELEX:32018R1139")

# From local file
with open("regulation.html", encoding="utf-8") as f:
    parser = EURLexParser(html_content=f.read())
```

#### Methods

##### `parse()`

```python
parse() -> tuple[list[RegulationChunk], dict]
```

Parse the document and return all chunks and the table of contents.

**Returns:** `(chunks, toc)` where `chunks` is a list of `RegulationChunk` objects and `toc` is a dictionary with `title` and `sections` keys.

##### `save_chunks(filepath)`

```python
save_chunks(filepath: str) -> None
```

Serialize all chunks to a JSON file using `RegulationChunk.to_dict()`.

##### `save_toc(filepath)`

```python
save_toc(filepath: str) -> None
```

Serialize the table of contents to a JSON file.

##### `print_toc()`

```python
print_toc() -> None
```

Print the indented table of contents to stdout.

##### `fetch()`

```python
fetch() -> str
```

Fetch the HTML source from the URL provided at construction. Returns the raw HTML string.

---

### RegulationChunk

Data class representing a single parsed content unit.

```python
from quiz_gen import RegulationChunk
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `section_type` | `SectionType` | Type of content unit |
| `number` | `str \| None` | Section number (e.g. `"1"`, `"IV"`) |
| `title` | `str \| None` | Full title including subtitle |
| `content` | `str` | Cleaned text content |
| `hierarchy_path` | `list[str]` | Ancestor titles from document root |
| `metadata` | `dict` | Additional fields: `id`, `subtitle`, etc. |

#### Methods

##### `to_dict()`

```python
to_dict() -> dict
```

Convert to a JSON-serializable dictionary. `section_type` is converted to its string value.

---

### SectionType

Enumeration of document content types.

```python
from quiz_gen import SectionType
```

| Value | String value | Description |
|-------|-------------|-------------|
| `SectionType.TITLE` | `"title"` | Document title |
| `SectionType.PREAMBLE` | `"preamble"` | Preamble section header |
| `SectionType.CITATION` | `"citation"` | Combined citation block |
| `SectionType.RECITAL` | `"recital"` | Individual recital |
| `SectionType.ENACTING_TERMS` | `"enacting_terms"` | Enacting terms section header |
| `SectionType.CHAPTER` | `"chapter"` | Chapter |
| `SectionType.SECTION` | `"section"` | Section within a chapter |
| `SectionType.ARTICLE` | `"article"` | Article (main content unit) |
| `SectionType.CONCLUDING_FORMULAS` | `"concluding_formulas"` | Concluding signatures |
| `SectionType.ANNEX` | `"annex"` | Annex |

---

## Agents

### AgentConfig

Dataclass that configures every agent in the multi-agent pipeline. API keys and base URLs are auto-loaded from environment variables when not provided directly.

```python
from quiz_gen.agents.config import AgentConfig
```

#### Constructor

All parameters are optional and have defaults. Unset API keys and base URLs are read from the environment.

```python
config = AgentConfig(
    openai_api_key="sk-...",       # or OPENAI_API_KEY env var
    anthropic_api_key="sk-ant-...", # or ANTHROPIC_API_KEY env var
    conceptual_provider="openai",
    conceptual_model="gpt-4o",
    verbose=True,
)
```

#### API key parameters

| Parameter | Environment variable |
|-----------|---------------------|
| `openai_api_key` | `OPENAI_API_KEY` |
| `anthropic_api_key` | `ANTHROPIC_API_KEY` |
| `mistral_api_key` | `MISTRAL_API_KEY` |
| `gemini_api_key` | `GEMINI_API_KEY` |
| `cohere_api_key` | `COHERE_API_KEY` |

#### Base URL parameters (optional)

| Parameter | Environment variable |
|-----------|---------------------|
| `openai_api_base` | `OPENAI_API_BASE` |
| `anthropic_api_base` | `ANTHROPIC_API_BASE` or `ANTHROPIC_BASE_URL` |
| `mistral_api_base` | `MISTRAL_API_BASE` |
| `gemini_api_base` | `GEMINI_API_BASE` |

#### Provider / model parameters

Default provider assignments per agent:

| Agent | Provider field | Default | Model field | Default |
|-------|---------------|---------|------------|---------|
| Conceptual | `conceptual_provider` | `"openai"` | `conceptual_model` | `"gpt-4o"` |
| Practical | `practical_provider` | `"anthropic"` | `practical_model` | `"claude-sonnet-4-20250514"` |
| Validator | `validator_provider` | `"openai"` | `validator_model` | `"gpt-4o"` |
| Refiner | `refiner_provider` | `"openai"` | `refiner_model` | `"gpt-4o"` |
| Judge | `judge_provider` | `"anthropic"` | `judge_model` | `"claude-sonnet-4-20250514"` |

Supported provider values: `openai`, `anthropic`, `google`, `mistral`, `cohere`.

#### Workflow parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `anthropic_max_tokens` | `int` | `4096` | Required max_tokens for Anthropic API calls |
| `auto_accept_valid` | `bool` | `False` | Accept questions automatically when validation passes |
| `save_intermediate_results` | `bool` | `True` | Save state between steps |
| `output_directory` | `str` | `"data/quizzes"` | Directory for saved quiz JSON files |
| `min_validation_score` | `int` | `6` | Minimum score out of 10 to pass validation |
| `strict_validation` | `bool` | `True` | Fail on any issue (not just score) |
| `max_retries` | `int` | `3` | Maximum API retry attempts |
| `verbose` | `bool` | `True` | Print step-by-step progress |

#### Methods

##### `validate()`

```python
validate() -> None
```

Check that the config is valid. Raises `ValueError` if required provider keys are missing or provider names are unrecognised.

##### `save(filepath, verbose=False)`

```python
save(filepath: str, verbose: bool = False) -> None
```

Write config to a JSON file. Prints the saved path when `verbose=True`.

##### `load(filepath)` (classmethod)

```python
AgentConfig.load(filepath: str) -> AgentConfig
```

Load and return an `AgentConfig` from a JSON file.

##### `print_summary()`

```python
print_summary() -> None
```

Print a formatted summary table of the current configuration to stdout.

---

### QuizGenerationWorkflow

LangGraph-based orchestration of the five-agent pipeline.

```python
from quiz_gen.agents.workflow import QuizGenerationWorkflow
```

#### Constructor

```python
QuizGenerationWorkflow(config: AgentConfig = None)
```

If `config` is `None`, a default `AgentConfig` is created (reads keys from environment variables).

#### Methods

##### `run(chunk, improvement_feedback=None)`

```python
run(chunk: dict, improvement_feedback: str = None) -> dict
```

Run the full pipeline for a single chunk.

**Parameters:**

- `chunk` — dictionary with the following keys: `content`, `title`, `number`, `section_type`, `hierarchy_path`, and optionally `metadata`. Use `RegulationChunk.to_dict()` to produce this from a parsed chunk.
- `improvement_feedback` — optional feedback string passed to the generators (used in human-in-the-loop iterations).

**Returns:** Full workflow state dictionary:

| Key | Type | Description |
|-----|------|-------------|
| `final_questions` | `list[dict]` | Accepted questions (0–2) |
| `judge_decision` | `str` | `accept_both`, `accept_conceptual`, `accept_practical`, or `reject_both` |
| `judge_reasoning` | `str` | Judge's explanation |
| `validation_results` | `list[dict]` | Validator output for each question |
| `conceptual_qa` | `dict` | Generated conceptual question |
| `practical_qa` | `dict` | Generated practical question |
| `refined_conceptual_qa` | `dict \| None` | Refined conceptual question (only if refined) |
| `refined_practical_qa` | `dict \| None` | Refined practical question (only if refined) |
| `errors` | `list[str]` | Any errors accumulated during execution |

##### `run_batch(chunks, save_output=True, output_dir="data/quizzes")`

```python
run_batch(
    chunks: list[dict],
    save_output: bool = True,
    output_dir: str = "data/quizzes",
) -> list[dict]
```

Run the workflow for each chunk in sequence. Prints a progress banner for each chunk. If `save_output` is `True`, saves accepted questions to a JSON file per chunk in `output_dir`.

**Returns:** List of state dictionaries, one per chunk.

---

### Individual agents

All agents can be used standalone outside of the workflow.

```python
from quiz_gen.agents.conceptual_generator import ConceptualGenerator
from quiz_gen.agents.practical_generator import PracticalGenerator
from quiz_gen.agents.validator import Validator
from quiz_gen.agents.refiner import Refiner
from quiz_gen.agents.judge import Judge
```

Each agent is instantiated directly from an `AgentConfig`:

```python
config = AgentConfig()
gen = ConceptualGenerator(config)
```

#### ConceptualGenerator / PracticalGenerator

```python
generate(chunk: dict, improvement_feedback: str = None) -> dict
```

Generate a multiple-choice question from a regulation chunk. Returns a question dict (see output format below).

#### Validator

```python
validate(qa: dict, chunk: dict) -> dict
validate_batch(qas: list[dict], chunk: dict) -> list[dict]
```

Validate one or more questions against the chunk they were generated from. Returns a validation result dict per question (see output format below).

#### Refiner

```python
refine(qa: dict, validation_result: dict, chunk: dict) -> dict
refine_batch(qas: list[dict], validation_results: list[dict], chunk: dict) -> list[dict]
```

Refine one or more questions based on validator feedback. Questions that already passed with a perfect score are returned unchanged (without `refiner_model`). Refined questions include a `refiner_model` field.

#### Judge

```python
judge(conceptual_qa: dict, practical_qa: dict, chunk: dict) -> dict
```

Make the final accept/reject decision. Returns `{"decision": "...", "reasoning": "..."}`.

---

## Output formats

### Question dict (generators / refiner output)

```json
{
  "question": "...",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "correct_answer": "A",
  "explanations": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "difficulty": "easy|medium|hard",
  "focus": "conceptual|practical",
  "generator": "conceptual|practical",
  "model": "gpt-4o"
}
```

Questions in `final_questions` also include a `source_reference` field populated by the workflow from the chunk's `hierarchy_path`.

### Validation result dict

```json
{
  "valid": true,
  "score": 10,
  "issues": [],
  "warnings": [],
  "checks_passed": {
    "has_4_options": true,
    "has_correct_answer": true,
    "has_all_explanations": true,
    "explanations_concise": true,
    "question_clear": true,
    "correct_explanation": true,
    "wrong_explanations_are_hints": true,
    "options_plausible": true,
    "question_unambiguous": true,
    "regulation_based": true
  }
}
```

### Judge output dict

```json
{
  "decision": "accept_both",
  "reasoning": "Both questions are high quality and test distinct skills."
}
```

Decision values: `accept_both`, `accept_conceptual`, `accept_practical`, `reject_both`.