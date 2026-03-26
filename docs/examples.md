# Examples

Working code examples for common quiz-gen use cases.

## 1. Parse a EUR-Lex document from URL

Parse the EU AI Act and inspect the results.

```python
from quiz_gen import EURLexParser

url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401689"
parser = EURLexParser(url=url)
chunks, toc = parser.parse()

# Print table of contents
parser.print_toc()

# Summary by section type
from collections import Counter
counts = Counter(c.section_type.value for c in chunks)
print("\nChunk summary:")
for section_type, count in sorted(counts.items()):
    print(f"  {section_type}: {count}")

# Save results
parser.save_chunks("data/processed/2024_1689_chunks.json")
parser.save_toc("data/processed/2024_1689_toc.json")
```

---

## 2. Parse a local HTML file

```python
from quiz_gen import EURLexParser

with open("data/raw/regulation.html", "r", encoding="utf-8") as f:
    html = f.read()

parser = EURLexParser(html_content=html)
chunks, toc = parser.parse()

print(f"Title: {toc['title']}")
print(f"Total chunks: {len(chunks)}")
```

---

## 3. Generate quiz questions for a single article

Uses the default provider configuration (OpenAI for most agents, Anthropic for practical and judge).

```python
from dotenv import load_dotenv
load_dotenv()

from quiz_gen import EURLexParser
from quiz_gen.agents.workflow import QuizGenerationWorkflow
from quiz_gen.agents.config import AgentConfig

# Parse a document
parser = EURLexParser(url="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139")
chunks, _ = parser.parse()

# Pick an article
from quiz_gen import SectionType
articles = [c for c in chunks if c.section_type == SectionType.ARTICLE]
article = articles[0]

print(f"Generating questions for: {article.title}\n")

# Run the workflow
config = AgentConfig()
workflow = QuizGenerationWorkflow(config)
result = workflow.run(article.to_dict())

# Print results
print(f"Judge decision: {result['judge_decision']}")
print(f"Reasoning: {result['judge_reasoning']}\n")

for q in result["final_questions"]:
    print(f"[{q['focus'].upper()}] {q['question']}")
    for letter, text in q["options"].items():
        marker = " <--" if letter == q["correct_answer"] else ""
        print(f"  {letter}. {text}{marker}")
    print(f"  Source: {q.get('source_reference', '')}\n")
```

---

## 4. Multi-provider configuration

Assign different providers and models to each agent.

```python
from dotenv import load_dotenv
load_dotenv()

from quiz_gen.agents.config import AgentConfig
from quiz_gen.agents.workflow import QuizGenerationWorkflow

config = AgentConfig(
    # Generators
    conceptual_provider="cohere",
    conceptual_model="command-r-plus-08-2024",
    practical_provider="google",
    practical_model="gemini-2.5-flash",
    # Validator
    validator_provider="openai",
    validator_model="gpt-4o",
    # Refiner
    refiner_provider="anthropic",
    refiner_model="claude-haiku-4-5-20251001",
    # Judge
    judge_provider="mistral",
    judge_model="mistral-large-latest",
    verbose=True,
)

workflow = QuizGenerationWorkflow(config)
```

---

## 5. Batch processing — parse and generate

Parse multiple documents and generate questions for every article.

```python
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from quiz_gen import EURLexParser, SectionType
from quiz_gen.agents.workflow import QuizGenerationWorkflow
from quiz_gen.agents.config import AgentConfig

config = AgentConfig(verbose=False)
workflow = QuizGenerationWorkflow(config)

for path in Path("data/raw").glob("*.html"):
    print(f"\nProcessing: {path.name}")

    with open(path, encoding="utf-8") as f:
        html = f.read()

    parser = EURLexParser(html_content=html)
    chunks, toc = parser.parse()

    # Save parsed output
    stem = path.stem
    parser.save_chunks(f"data/processed/{stem}_chunks.json")
    parser.save_toc(f"data/processed/{stem}_toc.json")

    # Generate questions for each article
    articles = [c for c in chunks if c.section_type == SectionType.ARTICLE]
    results = workflow.run_batch(
        [a.to_dict() for a in articles],
        save_output=True,
        output_dir=f"data/quizzes/{stem}",
    )

    accepted = sum(1 for r in results if r["final_questions"])
    print(f"  {len(articles)} articles → {accepted} with accepted questions")
```

---

## 6. Filter and display specific articles

```python
from quiz_gen import EURLexParser, SectionType

parser = EURLexParser(url="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139")
chunks, toc = parser.parse()

# Articles in CHAPTER I only
chapter1 = [
    c for c in chunks
    if c.section_type == SectionType.ARTICLE
    and any("CHAPTER I" in p for p in c.hierarchy_path)
]

print(f"Chapter I articles: {len(chapter1)}")
for a in chapter1:
    print(f"  Article {a.number}: {a.title}")
    print(f"    {a.content[:120]}...")
```

---

## 7. Human-in-the-loop refinement

Run one iteration and pass improvement feedback for a second pass.

```python
from dotenv import load_dotenv
load_dotenv()

from quiz_gen.agents.workflow import QuizGenerationWorkflow
from quiz_gen.agents.config import AgentConfig

config = AgentConfig()
workflow = QuizGenerationWorkflow(config)

chunk = {
    "section_type": "article",
    "number": "47",
    "title": "Article 47 - Delegated powers",
    "content": "The Commission shall be empowered to adopt delegated acts...",
    "hierarchy_path": ["Enacting Terms", "CHAPTER VIII", "Article 47"],
    "metadata": {},
}

# First pass
result = workflow.run(chunk)
print(f"First pass decision: {result['judge_decision']}")

# If output needs improvement, rerun with feedback
if result["judge_decision"] == "reject_both" or not result["final_questions"]:
    result = workflow.run(
        chunk,
        improvement_feedback="Focus on the practical implications for operators, not the legislative process.",
    )
    print(f"Second pass decision: {result['judge_decision']}")

for q in result["final_questions"]:
    print(f"\n[{q['focus']}] {q['question']}")
```

---

## 8. Load and inspect saved quiz JSON

```python
import json

with open("data/quizzes/quiz_47.json", "r", encoding="utf-8") as f:
    saved = json.load(f)

print(f"Chunk: {saved['chunk']['title']}")
print(f"Judge decision: {saved['judge_decision']}")
print(f"Questions saved: {len(saved['questions'])}")

for q in saved["questions"]:
    print(f"\n  Q: {q['question']}")
    print(f"  Correct: {q['correct_answer']} — {q['options'][q['correct_answer']]}")
    print(f"  Difficulty: {q['difficulty']}")
```

---

## 9. CLI batch loop

Process all HTML files in a directory from the command line:

```bash
for file in data/raw/*.html; do
    quiz-gen --output data/processed "$file"
done
```

With verbose output for the first file only:

```bash
quiz-gen --verbose --print-toc data/raw/2024_1689_AI_Act.html
```

Parse from URL and skip saving to inspect the TOC:

```bash
quiz-gen --no-save --print-toc \
  "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139"
```