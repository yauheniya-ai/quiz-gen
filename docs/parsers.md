# Document Parsers

The quiz-gen package provides specialized parsers for extracting structured content from regulatory and legal documents.

## EUR-Lex Parser

The `EURLexParser` is designed to parse European Union legal documents from the EUR-Lex database, extracting hierarchical structure, table of contents, and content chunks.

### Overview

The EUR-Lex parser processes HTML documents and extracts:

- **Document Title**: Main regulation/directive title with full citation
- **Table of Contents**: Complete hierarchical structure (3-4 levels)
- **Content Chunks**: Granular content units (title, citations, recitals, articles, annexes, concluding formulas)

All content is cleaned and formatted for optimal readability and downstream processing.

### Features

- ✅ Flexible hierarchy support (3-4 levels)
- ✅ Automatic structure detection
- ✅ Smart text cleaning (preserves lists and paragraphs)
- ✅ Both URL and local file input
- ✅ JSON export for chunks and TOC
- ✅ Complete metadata preservation
- ✅ Table extraction from annexes
- ✅ Cross-reference tracking

## Basic Usage

### Parsing from URL

```python
from quiz_gen.parsers.html.eu_lex_parser import EURLexParser

# Initialize parser with EUR-Lex URL
url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139"
parser = EURLexParser(url=url)

# Parse document
chunks, toc = parser.parse()

# Display summary
print(f"Extracted {len(chunks)} chunks")
print(f"Document: {toc['title']}")
```

### Parsing from Local File

```python
# Read local HTML file
with open('data/documents/regulation.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Initialize parser with HTML content
parser = EURLexParser(html_content=html_content)
chunks, toc = parser.parse()
```

### Saving Results

```python
# Save to JSON files
parser.save_chunks('output/chunks.json')
parser.save_toc('output/toc.json')

# Print formatted table of contents
parser.print_toc()
```

## Document Structure

EUR-Lex documents follow a hierarchical structure that the parser automatically detects:

### Level 0: Document Title
- Regulation/Directive full title
- Date and reference information

### Level 1: Major Sections
- **Preamble**: Citations and recitals
- **Enacting Terms**: Main regulatory content (chapters/articles)
- **Concluding Formulas**: Signatures and adoption information
- **Annexes**: Supplementary material (I-X)

### Level 2: Structural Divisions
- **Citation**: Combined citation paragraph
- **Recitals**: Numbered recitals (chunked individually)
- **Chapters**: Major content divisions

### Level 3: Sub-Divisions
- **Sections**: Optional subdivisions within chapters
- **Articles**: Main content units (chunked individually)

### Level 4: Nested Content (when sections exist)
- **Articles**: Within sections

## Content Chunks

The parser creates discrete chunks for the following content types:

### Title
```json
{
  "section_type": "title",
  "number": null,
  "title": "REGULATION (EU) 2018/1139...",
  "content": "Full regulation title and metadata",
  "hierarchy_path": ["REGULATION (EU) 2018/1139..."],
  "metadata": {"id": "tit_1"}
}
```

### Citation
All citations combined into a single chunk:
```json
{
  "section_type": "citation",
  "number": null,
  "title": "Citation",
  "content": "Having regard to...\n\nHaving regard to...",
  "hierarchy_path": ["REGULATION...", "Preamble", "Citation"],
  "metadata": {"id": "cit_1", "citation_ids": ["cit_1", "cit_2", ...]}
}
```

### Recitals
Individual chunks for each recital:
```json
{
  "section_type": "recital",
  "number": "1",
  "title": "Recital 1",
  "content": "A high and uniform level of civil aviation...",
  "hierarchy_path": ["REGULATION...", "Preamble", "Recital 1"],
  "metadata": {"id": "rct_1"}
}
```

### Articles
Individual chunks for each article:
```json
{
  "section_type": "article",
  "number": "1",
  "title": "Article 1 - Subject matter and objectives",
  "content": "1. The principal objective...\n\n2. This Regulation...",
  "hierarchy_path": ["REGULATION...", "CHAPTER I - PRINCIPLES", "Article 1..."],
  "metadata": {"id": "art_1", "subtitle": "Subject matter and objectives"}
}
```

### Annexes
Individual chunks for each annex (including tables):
```json
{
  "section_type": "annex",
  "number": "I",
  "title": "ANNEX I - Aircraft referred to...",
  "content": "Historic aircraft meeting...",
  "hierarchy_path": ["REGULATION...", "ANNEX I - Aircraft..."],
  "metadata": {"id": "anx_I", "subtitle": "Aircraft referred to..."}
}
```

### Concluding Formulas
```json
{
  "section_type": "concluding_formulas",
  "number": null,
  "title": "Concluding formulas",
  "content": "This Regulation shall be binding...",
  "hierarchy_path": ["REGULATION...", "Concluding formulas"],
  "metadata": {"id": "fnp_1"}
}
```

## Advanced Usage

### Filtering Chunks by Type

```python
from quiz_gen.models.chunk import SectionType

# Get only articles
articles = [c for c in chunks if c.section_type == SectionType.ARTICLE]

# Get only recitals
recitals = [c for c in chunks if c.section_type == SectionType.RECITAL]

# Get content from specific chapter
chapter_1 = [c for c in chunks if 'CHAPTER I' in ' > '.join(c.hierarchy_path)]
```

### Working with Hierarchy

```python
# Print hierarchy for each chunk
for chunk in chunks:
    hierarchy = ' > '.join(chunk.hierarchy_path)
    print(f"{hierarchy}")
    
# Find parent chapter of an article
article = chunks[100]  # Some article
parent = article.hierarchy_path[-2] if len(article.hierarchy_path) > 1 else None
```

### Accessing Metadata

```python
# Navigation IDs for linking to original document
for chunk in chunks:
    doc_id = chunk.metadata.get('id')
    # Use to construct URL: base_url + "#" + doc_id
    
# Article subtitles
articles = [c for c in chunks if c.section_type == SectionType.ARTICLE]
for article in articles:
    subtitle = article.metadata.get('subtitle', '')
    print(f"{article.title}: {subtitle}")
```

### Custom Processing

```python
# Extract specific articles by number
def get_article(chunks, number):
    for chunk in chunks:
        if chunk.section_type == SectionType.ARTICLE and chunk.number == number:
            return chunk
    return None

article_5 = get_article(chunks, "5")

# Search content
def search_chunks(chunks, query):
    return [c for c in chunks if query.lower() in c.content.lower()]

safety_chunks = search_chunks(chunks, "safety")
```

## Text Formatting

The parser applies intelligent text cleaning:

### List Formatting
```
Original HTML:           →    Cleaned Output:
(a)                           (a) contribute to the policy
                              
contribute to the policy      (b) facilitate the movement
                              
(b)

facilitate the movement
```

### Paragraph Formatting
```
Original HTML:           →    Cleaned Output:
1.                            1. The principal objective...
                              
The principal objective       2. This Regulation aims to...

2.

This Regulation aims to
```

## Table of Contents Structure

The TOC JSON structure:

```json
{
  "title": "REGULATION (EU) 2018/1139 OF THE EUROPEAN PARLIAMENT...",
  "sections": [
    {
      "type": "preamble",
      "title": "Preamble",
      "children": [
        {"type": "citation", "title": "Citation"},
        {"type": "recital", "number": "1", "title": "Recital 1"},
        {"type": "recital", "number": "2", "title": "Recital 2"}
      ]
    },
    {
      "type": "enacting_terms",
      "title": "Enacting Terms",
      "children": [
        {
          "type": "chapter",
          "number": "I",
          "title": "CHAPTER I - PRINCIPLES",
          "children": [
            {"type": "article", "number": "1", "title": "Article 1 - Subject..."},
            {"type": "article", "number": "2", "title": "Article 2 - Scope"}
          ]
        },
        {
          "type": "chapter",
          "number": "III",
          "title": "CHAPTER III - SUBSTANTIVE REQUIREMENTS",
          "children": [
            {
              "type": "section",
              "number": "I",
              "title": "SECTION I - Airworthiness...",
              "children": [
                {"type": "article", "number": "9", "title": "Article 9..."}
              ]
            }
          ]
        }
      ]
    },
    {
      "type": "concluding_formulas",
      "title": "Concluding formulas"
    },
    {
      "type": "annex",
      "number": "I",
      "title": "ANNEX I - Aircraft referred to..."
    }
  ]
}
```

## Supported Document Types

The parser is optimized for EUR-Lex HTML documents:

### Fully Supported
- ✅ EU Regulations
- ✅ EU Directives  
- ✅ EU Decisions
- ✅ Aviation regulations (EASA)
- ✅ Multi-level hierarchies (chapters, sections, articles)
- ✅ Annexes (text and tables)

### Required HTML Structure
Documents must contain:
- `<div class="eli-main-title">` - Document title
- `<div class="eli-subdivision" id="cit_*">` - Citations
- `<div class="eli-subdivision" id="rct_*">` - Recitals
- `<div id="cpt_*">` - Chapters
- `<div class="eli-subdivision" id="art_*">` - Articles
- `<div class="eli-container" id="anx_*">` - Annexes

## API Reference

### EURLexParser

Main parser class for EUR-Lex documents.

#### Constructor

```python
EURLexParser(url: str = None, html_content: str = None)
```

**Parameters:**
- `url` (str, optional): URL of EUR-Lex document to fetch
- `html_content` (str, optional): HTML content string for parsing

**Raises:**
- `ValueError`: If neither url nor html_content provided

#### Methods

##### parse()
```python
parse() -> tuple[List[RegulationChunk], Dict]
```
Parse document and return chunks and table of contents.

**Returns:**
- Tuple of (chunks list, TOC dictionary)

**Raises:**
- `ValueError`: If no content available to parse
- `HTTPError`: If URL fetch fails

##### fetch()
```python
fetch() -> str
```
Fetch HTML content from URL.

**Returns:**
- HTML content string

##### save_chunks()
```python
save_chunks(filepath: str) -> None
```
Save chunks to JSON file.

**Parameters:**
- `filepath` (str): Output file path

##### save_toc()
```python
save_toc(filepath: str) -> None
```
Save table of contents to JSON file.

**Parameters:**
- `filepath` (str): Output file path

##### print_toc()
```python
print_toc() -> None
```
Print formatted table of contents to console.

### RegulationChunk

Data class representing a parsed content chunk.

#### Attributes

- `section_type` (SectionType): Type of section
- `number` (str | None): Section number
- `title` (str): Full title with subtitle
- `content` (str): Text content
- `hierarchy_path` (List[str]): Parent sections list
- `metadata` (Dict): Additional structured data

#### Methods

##### to_dict()
```python
to_dict() -> Dict
```
Convert chunk to dictionary for JSON serialization.

### SectionType

Enumeration of document section types.

#### Values

- `TITLE`: Document title
- `PREAMBLE`: Preamble section
- `CITATION`: Citation paragraph
- `RECITAL`: Individual recital
- `ENACTING_TERMS`: Main content section
- `CHAPTER`: Chapter division
- `SECTION`: Section within chapter
- `ARTICLE`: Article (main content unit)
- `CONCLUDING_FORMULAS`: Concluding signatures
- `ANNEX`: Annex section

## Performance Considerations

### Memory Usage
- Large regulations (500+ pages) may generate 500+ chunks
- Each chunk typically 100-2000 bytes
- Total memory: ~1-5 MB per regulation

### Processing Time
- Typical regulation: 2-5 seconds
- Network fetch: 1-3 seconds (if using URL)
- Parsing: 1-2 seconds
- Large documents (10+ annexes): up to 10 seconds

### Optimization Tips

```python
# For batch processing, reuse parser instance
parser = EURLexParser()
for html_file in html_files:
    with open(html_file) as f:
        parser.html_content = f.read()
    chunks, toc = parser.parse()
    # Process chunks
    parser.chunks.clear()  # Clear for next iteration
```

## Troubleshooting

### Common Issues

**Issue: Empty chunks or missing content**
```python
# Check if HTML has correct EUR-Lex structure
parser = EURLexParser(html_content=html)
if not parser.soup.find('div', class_='eli-main-title'):
    print("Not a valid EUR-Lex document")
```

**Issue: Incorrect hierarchy**
```python
# Verify chapter/section IDs match EUR-Lex format
chapters = parser.soup.find_all('div', id=re.compile(r'^cpt_'))
print(f"Found {len(chapters)} chapters")
```

**Issue: Text formatting problems**
```python
# Check cleaned text
from quiz_gen.parsers.html.eu_lex_parser import EURLexParser
text = "test (a)\n\ncontent"
cleaned = EURLexParser._clean_combined_text(text)
print(repr(cleaned))  # Should be: 'test (a) content'
```

## Examples

See the [Examples](examples.md) page for complete working examples including:
- Batch processing multiple documents
- Building a searchable database
- Generating comparative analyses
- Creating study guides

## Next Steps

- [CLI Usage](cli.md) - Command-line interface documentation
- [API Reference](api.md) - Complete API documentation  
- [Examples](examples.md) - Practical usage examples
