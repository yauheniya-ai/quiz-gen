# Getting Started

This guide will help you install Quiz-Gen and parse your first document in minutes.

## Installation

### Using pip (Recommended)

Install the latest stable version from PyPI:

```bash
pip install quiz-gen
```

### Verify Installation

Check that the installation was successful:

```bash
quiz-gen --version
```

You should see:
```
quiz-gen 0.1.1
```

### Development Installation

For development or contributing, clone the repository and install with development dependencies:

```bash
git clone https://github.com/yauheniya-ai/quiz-gen.git
cd quiz-gen
pip install -e ".[dev]"
```

## Your First Parse

Let's parse a real EUR-Lex regulation and extract its structure.

### Using the Command Line

The simplest way to get started is using the CLI:

```bash
quiz-gen https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139
```

This will:
1. Download the EASA Basic Regulation
2. Parse it into structured chunks
3. Generate a table of contents
4. Save two JSON files in the current directory

**Output files:**
- `2018_1139_chunks.json` - All content chunks with metadata
- `2018_1139_toc.json` - Complete table of contents

### Using Python Code

For programmatic access, use the Python API:

```python
from quiz_gen.parsers.html.eu_lex_parser import EURLexParser

# Parse from URL
url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139"
parser = EURLexParser(url=url)
chunks, toc = parser.parse()

# Print summary
print(f"Document: {toc['title']}")
print(f"Total chunks: {len(chunks)}")
print(f"First article: {chunks[90].number} - {chunks[90].title}")
```

### Parsing Local Files

If you have HTML files saved locally:

**Command line:**
```bash
quiz-gen data/documents/regulation.html
```

**Python:**
```python
from quiz_gen.parsers.html.eu_lex_parser import EURLexParser

parser = EURLexParser(file_path="data/documents/regulation.html")
chunks, toc = parser.parse()
```

## Understanding the Output

### Content Chunks

Each document is split into chunks representing logical units:

```json
{
  "section_type": "article",
  "number": "1",
  "title": "Subject matter and scope",
  "subtitle": null,
  "content": "This Regulation lays down common rules...",
  "navigation_id": "art_1",
  "hierarchy_path": ["Enacting Terms", "CHAPTER I", "Article 1"]
}
```

**Chunk types:**
- `title` - Document title
- `citation` - Combined legal citations
- `recital` - Preamble recitals
- `article` - Main regulatory articles
- `annex` - Appendices (including tables)
- `concluding_formulas` - Signatures and adoption info

### Table of Contents

The TOC provides a hierarchical navigation structure:

```json
{
  "title": "Regulation (EU) 2018/1139",
  "hierarchy": {
    "Enacting Terms": {
      "CHAPTER I - GENERAL PROVISIONS": {
        "Article 1": {"id": "art_1", "type": "article"},
        "Article 2": {"id": "art_2", "type": "article"}
      }
    }
  }
}
```

## CLI Options

Customize parsing behavior with command-line flags:

### Specify Output Directory

```bash
quiz-gen --output data/processed regulation.html
```

### Custom Output Filenames

```bash
quiz-gen --chunks articles.json --toc structure.json regulation.html
```

### Preview TOC Without Saving

```bash
quiz-gen --print-toc --no-save https://eur-lex.europa.eu/legal-content/...
```

This prints the table of contents to console without saving any files.

### Verbose Mode

```bash
quiz-gen --verbose regulation.html
```

Shows detailed parsing progress:
```
Parsing document...
  ✓ Title extracted
  ✓ Preamble: 1 citation, 88 recitals
  ✓ Enacting terms: 141 articles
  ✓ Annexes: 10
Total chunks: 242
```

### Get Help

```bash
quiz-gen --help
```

Shows all available options with descriptions.

## Working With Parsed Data

### Loading JSON Files

```python
import json
from quiz_gen.models.chunk import Chunk

# Load chunks
with open("2018_1139_chunks.json", "r", encoding="utf-8") as f:
    chunks_data = json.load(f)

# Convert to Chunk objects
chunks = [Chunk(**c) for c in chunks_data]

# Load TOC
with open("2018_1139_toc.json", "r", encoding="utf-8") as f:
    toc = json.load(f)
```

### Filtering Content

```python
# Get all articles
articles = [c for c in chunks if c.section_type.value == "article"]

# Get recitals
recitals = [c for c in chunks if c.section_type.value == "recital"]

# Get annexes
annexes = [c for c in chunks if c.section_type.value == "annex"]

# Find specific article by number
article_5 = next(c for c in chunks if c.number == "5")
print(f"{article_5.title}: {article_5.content[:100]}...")
```

### Searching Content

```python
# Find articles about "safety"
safety_articles = [
    c for c in chunks 
    if c.section_type.value == "article" 
    and "safety" in c.content.lower()
]

for article in safety_articles:
    print(f"Article {article.number}: {article.title}")
```

### Navigating Hierarchy

```python
# Get chapters from TOC
enacting = toc["hierarchy"]["Enacting Terms"]
chapters = list(enacting.keys())

print("Document structure:")
for chapter in chapters:
    articles = enacting[chapter]
    print(f"  {chapter}: {len(articles)} articles")
```

## Common Patterns

### Batch Processing

Process multiple documents:

```python
from pathlib import Path
from quiz_gen.parsers.html.eu_lex_parser import EURLexParser

documents = Path("data/documents/html").glob("*.html")

for doc_path in documents:
    parser = EURLexParser(file_path=str(doc_path))
    chunks, toc = parser.parse()
    
    # Save with custom names
    base = doc_path.stem
    parser.save_to_json(
        chunks=chunks,
        toc=toc,
        chunks_file=f"data/processed/{base}_chunks.json",
        toc_file=f"data/processed/{base}_toc.json"
    )
    print(f"✓ Processed {base}: {len(chunks)} chunks")
```

### Extract Specific Sections

```python
from quiz_gen.parsers.html.eu_lex_parser import EURLexParser

url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139"
parser = EURLexParser(url=url)
chunks, toc = parser.parse()

# Get only Chapter I articles
chapter1_articles = [
    c for c in chunks
    if c.section_type.value == "article"
    and "CHAPTER I" in c.hierarchy_path
]

print(f"Chapter I has {len(chapter1_articles)} articles")
for article in chapter1_articles:
    print(f"  - Article {article.number}: {article.title}")
```

### Building a Database

```python
import sqlite3
from quiz_gen.parsers.html.eu_lex_parser import EURLexParser

# Parse document
url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139"
parser = EURLexParser(url=url)
chunks, toc = parser.parse()

# Create database
conn = sqlite3.connect("regulations.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY,
        regulation TEXT,
        article_number TEXT,
        title TEXT,
        content TEXT,
        navigation_id TEXT
    )
""")

# Insert articles
for chunk in chunks:
    if chunk.section_type.value == "article":
        cursor.execute("""
            INSERT INTO articles (regulation, article_number, title, content, navigation_id)
            VALUES (?, ?, ?, ?, ?)
        """, (toc["title"], chunk.number, chunk.title, chunk.content, chunk.navigation_id))

conn.commit()
conn.close()

print(f"Database created with {len([c for c in chunks if c.section_type.value == 'article'])} articles")
```

## Document Structure

Quiz-Gen extracts documents with flexible hierarchies:

### Standard 3-Level Structure

```
Title (Level 0)
└── Enacting Terms (Level 1)
    └── Chapter (Level 2)
        └── Article (Level 3)
```

### Extended 4-Level Structure

Some regulations include sections:

```
Title (Level 0)
└── Enacting Terms (Level 1)
    └── Chapter (Level 2)
        └── Section (Level 3)
            └── Article (Level 4)
```

The parser automatically detects which structure is used.

### Complete Document Breakdown

```
Document
├── Title (Level 0)
│   └── Main regulation title
│
├── Preamble (Level 1)
│   ├── Citation (combined, single chunk)
│   └── Recitals (numbered, individual chunks)
│
├── Enacting Terms (Level 1)
│   └── Chapters (Level 2)
│       ├── Articles (Level 3)
│       └── Sections (Level 3, when present)
│           └── Articles (Level 4)
│
├── Concluding Formulas (Level 1)
│   └── Signatures and adoption info
│
└── Annexes (Level 1)
    └── Numbered annexes (I-X, etc.)
        ├── Text content
        └── Tables (formatted as pipe-separated)
```

## Text Formatting

The parser automatically cleans and formats text:

### List Items

Raw HTML:
```html
<p>(a)</p>
<p>contribute to...</p>
```

Cleaned output:
```
(a) contribute to...
```

### Numbered Paragraphs

Raw HTML:
```html
<p>1.</p>
<p>The principal...</p>
```

Cleaned output:
```
1. The principal...
```

### Tables in Annexes

Tables are preserved with pipe-separated format:

```
| Column 1 | Column 2 | Column 3 |
| Value A | Value B | Value C |
| Value D | Value E | Value F |
```

This makes tables machine-readable while preserving structure.

## Troubleshooting

### "No such file or directory"

**Problem:** File path is incorrect.

**Solution:**
```bash
# Use absolute path
quiz-gen /Users/username/Documents/regulation.html

# Or relative from current directory
cd /Users/username/Documents
quiz-gen regulation.html
```

### "Invalid URL or empty document"

**Problem:** URL is incorrect or document can't be accessed.

**Solution:**
- Check URL is correct and accessible in browser
- Ensure you have internet connection
- Try saving HTML and parsing locally

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'quiz_gen'`

**Solution:**
```bash
# Reinstall package
pip install --upgrade quiz-gen

# Or in development mode
pip install -e .
```

### Empty Output Files

**Problem:** Chunks or TOC files are empty or contain `[]`.

**Solution:**
- Check that HTML file has EUR-Lex format
- Verify document has expected structure
- Try with a known-working URL (e.g., CELEX:32018R1139)
- Use `--verbose` to see what's being extracted

### Permission Denied

**Problem:** Can't write output files.

**Solution:**
```bash
# Specify writable directory
quiz-gen --output ~/Documents regulation.html

# Or check directory permissions
chmod 755 output_directory
```

## Next Steps

Now that you've parsed your first document:

- **[Parsers Guide](parsers.md)** - Deep dive into parser features and options
- **[API Reference](api.md)** - Complete class and method documentation
- **[Examples](examples.md)** - More advanced usage patterns and integrations

## Need Help?

- **Issues**: [GitHub Issue Tracker](https://github.com/yauheniya-ai/quiz-gen/issues)
- **Documentation**: [Full Documentation](https://quiz-gen.readthedocs.io)
- **PyPI**: [Package Page](https://pypi.org/project/quiz-gen)

Happy parsing! 🚀
