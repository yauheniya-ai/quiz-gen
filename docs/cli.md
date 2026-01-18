# Command-Line Interface

The Quiz-Gen CLI provides a powerful and user-friendly command-line interface for parsing EUR-Lex documents and extracting structured content.

## Installation

The CLI is automatically available after installing the package:

```bash
pip install quiz-gen
```

Verify installation:

```bash
quiz-gen --version
```

## Basic Usage

### Quick Start

Parse a document from URL:

```bash
quiz-gen https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139
```

Parse a local HTML file:

```bash
quiz-gen data/documents/regulation.html
```

### Command Syntax

```
quiz-gen [OPTIONS] INPUT
```

**Arguments:**
- `INPUT` - URL or file path to EUR-Lex HTML document (required)

## Options Reference

### Input/Output Options

#### `INPUT` (required)
The source document to parse. Can be:
- **URL**: `https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139`
- **Local file**: `data/documents/regulation.html` or `/absolute/path/to/file.html`

```bash
# Parse from URL
quiz-gen https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139

# Parse from relative path
quiz-gen data/documents/regulation.html

# Parse from absolute path
quiz-gen /Users/username/Documents/regulation.html
```

#### `-o, --output DIRECTORY`
Output directory for generated JSON files.

**Default:** `data/processed`

```bash
# Save to custom directory
quiz-gen --output results regulation.html

# Save to absolute path
quiz-gen --output /Users/username/output regulation.html

# Save to current directory
quiz-gen --output . regulation.html
```

The directory will be created automatically if it doesn't exist.

#### `--chunks FILENAME`
Custom filename for chunks JSON output.

**Default:** `<document-id>_chunks.json`

```bash
# Custom chunks filename
quiz-gen --chunks my_articles.json regulation.html

# Will create: data/processed/my_articles.json
```

When not specified, the filename is generated from:
- **URL**: CELEX number (e.g., `32018R1139_chunks.json`)
- **File**: File stem (e.g., `regulation_chunks.json`)

#### `--toc FILENAME`
Custom filename for table of contents JSON output.

**Default:** `<document-id>_toc.json`

```bash
# Custom TOC filename
quiz-gen --toc my_structure.json regulation.html

# Will create: data/processed/my_structure.json
```

#### `--no-save`
Parse document and show statistics but don't save any files.

```bash
# Preview parsing results without saving
quiz-gen --no-save regulation.html
```

Useful for:
- Testing document compatibility
- Previewing chunk counts
- Checking document structure

### Display Options

#### `--print-toc`
Print formatted table of contents to console after parsing.

```bash
# Show TOC in console
quiz-gen --print-toc regulation.html
```

Output example:
```
Regulation (EU) 2018/1139
├── Preamble
│   ├── Citation
│   └── Recitals (88)
├── Enacting Terms
│   ├── CHAPTER I - GENERAL PROVISIONS
│   │   ├── Article 1 - Subject matter and scope
│   │   └── Article 2 - Definitions
...
```

Can be combined with `--no-save` to only display TOC:

```bash
quiz-gen --print-toc --no-save regulation.html
```

#### `--verbose`
Enable detailed output showing parsing progress and errors.

```bash
quiz-gen --verbose regulation.html
```

Output includes:
- Document fetching/reading status
- Parsing progress for each section
- Detailed error messages with stack traces
- File saving confirmations

Example output:
```
Fetching document from URL: https://eur-lex.europa.eu/...
Parsing document...
  ✓ Title extracted
  ✓ Preamble: 1 citation, 88 recitals
  ✓ Enacting terms: 10 chapters, 141 articles
  ✓ Concluding formulas: 1
  ✓ Annexes: 10

✓ Successfully parsed document
  Title: Regulation (EU) 2018/1139 of the European Parliament...
  Total chunks: 242
    title: 1
    citation: 1
    recital: 88
    article: 141
    concluding_formulas: 1
    annex: 10

✓ Files saved to: data/processed
```

#### `-v, --version`
Display version information and exit.

```bash
quiz-gen --version
```

Output:
```
quiz-gen 0.1.1
```

#### `-h, --help`
Show help message with all options and examples.

```bash
quiz-gen --help
```

## Examples

### Basic Parsing

Parse a regulation from EUR-Lex:

```bash
quiz-gen https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139
```

**Output:**
- `data/processed/32018R1139_chunks.json`
- `data/processed/32018R1139_toc.json`

### Custom Output Location

Save to specific directory:

```bash
quiz-gen --output regulations/easa regulation.html
```

**Output:**
- `regulations/easa/regulation_chunks.json`
- `regulations/easa/regulation_toc.json`

### Custom Filenames

Use custom names for both output files:

```bash
quiz-gen --output data \
  --chunks easa_articles.json \
  --toc easa_structure.json \
  regulation.html
```

**Output:**
- `data/easa_articles.json`
- `data/easa_structure.json`

### Preview Without Saving

Check document structure before saving:

```bash
quiz-gen --print-toc --no-save regulation.html
```

Shows full TOC in console without creating files.

### Batch Processing

Process multiple documents:

```bash
# Using a shell loop
for file in data/documents/*.html; do
  quiz-gen --output data/processed "$file"
done
```

Or with custom naming:

```bash
#!/bin/bash
for file in data/documents/*.html; do
  base=$(basename "$file" .html)
  quiz-gen --output data/processed \
    --chunks "${base}_articles.json" \
    --toc "${base}_toc.json" \
    "$file"
done
```

### Pipeline Integration

Use in data processing pipelines:

```bash
# Download, parse, and extract articles
curl -s "https://eur-lex.europa.eu/...uri=CELEX:32018R1139" > temp.html && \
  quiz-gen --output . temp.html && \
  rm temp.html
```

Check if parsing succeeded:

```bash
quiz-gen regulation.html
if [ $? -eq 0 ]; then
  echo "Parsing successful"
  # Continue processing...
else
  echo "Parsing failed"
  exit 1
fi
```

### Verbose Mode for Debugging

Get detailed output for troubleshooting:

```bash
quiz-gen --verbose --print-toc regulation.html
```

Shows:
- Detailed parsing progress
- Chunk type counts
- Full TOC structure
- Error stack traces (if any)

### Current Directory Output

Save files in current working directory:

```bash
quiz-gen --output . regulation.html
```

## Output Files

### Chunks JSON

Contains all document content split into logical chunks.

**Filename pattern:** `<document-id>_chunks.json`

**Structure:**
```json
[
  {
    "section_type": "title",
    "number": null,
    "title": "Regulation (EU) 2018/1139",
    "subtitle": null,
    "content": "Regulation (EU) 2018/1139 of the European Parliament...",
    "navigation_id": "title",
    "hierarchy_path": []
  },
  {
    "section_type": "article",
    "number": "1",
    "title": "Subject matter and scope",
    "subtitle": null,
    "content": "This Regulation lays down common rules...",
    "navigation_id": "art_1",
    "hierarchy_path": ["Enacting Terms", "CHAPTER I", "Article 1"]
  }
]
```

### Table of Contents JSON

Hierarchical navigation structure of the document.

**Filename pattern:** `<document-id>_toc.json`

**Structure:**
```json
{
  "title": "Regulation (EU) 2018/1139",
  "hierarchy": {
    "Preamble": {
      "Citation": {
        "id": "cit_1",
        "type": "citation"
      },
      "Recital 1": {
        "id": "rec_1",
        "type": "recital"
      }
    },
    "Enacting Terms": {
      "CHAPTER I - GENERAL PROVISIONS": {
        "Article 1": {
          "id": "art_1",
          "type": "article"
        }
      }
    }
  }
}
```

## Exit Codes

The CLI returns standard exit codes:

- **0** - Success: Document parsed and files saved
- **1** - Error: Parsing failed or invalid input

Use in scripts:

```bash
if quiz-gen regulation.html; then
  echo "Success"
else
  echo "Failed with exit code $?"
fi
```

## Error Handling

### Common Errors

#### File Not Found

```
Error: File not found: data/regulation.html
```

**Solution:** Check file path is correct and file exists.

#### Invalid URL

```
Error: Invalid URL or empty document
```

**Solutions:**
- Verify URL is correct and accessible
- Check internet connection
- Try downloading HTML and parsing locally

#### Permission Denied

```
Error: [Errno 13] Permission denied: 'data/processed'
```

**Solutions:**
```bash
# Create directory manually
mkdir -p data/processed

# Or use writable location
quiz-gen --output ~/Documents regulation.html
```

#### Parse Errors

```
Error: Failed to parse document structure
```

**Solution:** Use `--verbose` to see detailed error:

```bash
quiz-gen --verbose regulation.html
```

### Debugging Tips

1. **Use verbose mode** to see what's happening:
   ```bash
   quiz-gen --verbose regulation.html
   ```

2. **Preview without saving** to test parsing:
   ```bash
   quiz-gen --no-save regulation.html
   ```

3. **Check document structure** with TOC:
   ```bash
   quiz-gen --print-toc --no-save regulation.html
   ```

4. **Test with known document** to verify installation:
   ```bash
   quiz-gen https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139
   ```

## Performance

### Typical Processing Times

| Document Size | Articles | Processing Time |
|--------------|----------|-----------------|
| Small (< 50 articles) | < 50 | < 5 seconds |
| Medium (50-150 articles) | 50-150 | 5-15 seconds |
| Large (> 150 articles) | > 150 | 15-30 seconds |

Times include:
- Document download/reading
- HTML parsing
- Content extraction
- Text cleaning
- JSON serialization

### Memory Usage

Memory usage scales with document size:

- **Small documents**: < 50 MB
- **Medium documents**: 50-100 MB
- **Large documents**: 100-200 MB

The parser processes documents in memory, so ensure adequate RAM for large documents.

### Network Performance

For URL parsing:
- Download time depends on internet speed
- EUR-Lex documents are typically 200 KB - 2 MB
- Use local files for batch processing to avoid network overhead

## Integration

### Python Scripts

```python
import subprocess
import sys

result = subprocess.run(
    ["quiz-gen", "--output", "data", "regulation.html"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("Success:", result.stdout)
else:
    print("Error:", result.stderr, file=sys.stderr)
```

### Makefiles

```makefile
.PHONY: parse-all

parse-all:
	@for file in data/raw/*.html; do \
		quiz-gen --output data/processed "$$file"; \
	done

parse-verbose:
	quiz-gen --verbose --print-toc $(FILE)
```

### CI/CD Pipelines

```yaml
# GitHub Actions example
- name: Parse EUR-Lex documents
  run: |
    pip install quiz-gen
    quiz-gen --output artifacts regulation.html
    
- name: Upload results
  uses: actions/upload-artifact@v3
  with:
    name: parsed-documents
    path: artifacts/*.json
```

## Advanced Usage

### Environment Variables

While not directly supported, you can use shell variables:

```bash
OUTPUT_DIR="data/processed"
VERBOSE_FLAG="--verbose"

quiz-gen $VERBOSE_FLAG --output $OUTPUT_DIR regulation.html
```

### Process Substitution

Parse from curl output:

```bash
quiz-gen <(curl -s "https://eur-lex.europa.eu/...uri=CELEX:32018R1139")
```

### JSON Processing

Pipe output to jq for analysis:

```bash
# Count articles by chapter
quiz-gen --no-save regulation.html 2>&1 | grep "article:"
```

Or process saved JSON:

```bash
quiz-gen regulation.html
jq '[.[] | select(.section_type == "article")] | length' \
  data/processed/regulation_chunks.json
```

### Parallel Processing

Process multiple documents in parallel:

```bash
# GNU parallel
parallel quiz-gen --output data/processed ::: data/raw/*.html

# xargs (macOS/Linux)
ls data/raw/*.html | xargs -n 1 -P 4 quiz-gen --output data/processed
```

## Best Practices

### File Organization

Recommended directory structure:

```
project/
├── data/
│   ├── raw/              # Original HTML files
│   ├── processed/        # Parsed JSON output (default)
│   └── documents/
│       └── html/         # Downloaded documents
├── scripts/
│   └── parse_all.sh      # Batch processing scripts
└── results/              # Final analysis output
```

### Naming Conventions

Use consistent naming for outputs:

```bash
# Good: includes document ID
quiz-gen --chunks 2018_1139_content.json regulation.html

# Better: includes date and version
quiz-gen --chunks 2018_1139_v1_20260118_content.json regulation.html
```

### Error Handling in Scripts

```bash
#!/bin/bash
set -e  # Exit on error

for file in data/raw/*.html; do
  if ! quiz-gen --output data/processed "$file"; then
    echo "Failed to parse: $file" >> errors.log
  fi
done
```

### Version Pinning

For reproducible environments:

```bash
# requirements.txt
quiz-gen==0.1.1
```

```bash
pip install -r requirements.txt
```

## Troubleshooting

### CLI Not Found

```bash
quiz-gen: command not found
```

**Solutions:**

1. Verify installation:
   ```bash
   pip list | grep quiz-gen
   ```

2. Reinstall:
   ```bash
   pip install --force-reinstall quiz-gen
   ```

3. Check PATH:
   ```bash
   which quiz-gen
   python -m quiz_gen.cli --version
   ```

### Wrong Version

```bash
# Check current version
quiz-gen --version

# Upgrade to latest
pip install --upgrade quiz-gen
```

### Import Errors

If you see module import errors, reinstall dependencies:

```bash
pip install --upgrade beautifulsoup4 lxml requests
```

## Related Documentation

- **[Getting Started](getting-started.md)** - Installation and first steps
- **[Parsers](parsers.md)** - Detailed parser documentation
- **[API Reference](api.md)** - Python API documentation
- **[Examples](examples.md)** - Advanced usage examples

## Support

For CLI-specific issues:

1. Check this documentation
2. Run with `--verbose` for detailed errors
3. Report issues at [GitHub Issue Tracker](https://github.com/yauheniya-ai/quiz-gen/issues)
4. Include:
   - Command used
   - Complete error message
   - Output from `quiz-gen --version`
   - Sample document (if possible)
