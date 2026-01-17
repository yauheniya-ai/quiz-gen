#!/usr/bin/env python3
"""
Example: Parsing EASA Regulation (EU) 2018/1139
Chunks the document into structured pieces with proper citations.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.quiz_gen.parsers.html.eu_lex_parser import EURLexParser


def main():
    """Parse and chunk the EASA regulation document"""
    
    # EASA Regulation (EU) 2018/1139
    url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139"
    
    print(f"Parsing: {url}\n")
    
    # Parse document - returns (chunks, toc)
    parser = EURLexParser(url=url)
    chunks, toc = parser.parse()
    
    # Display TOC
    parser.print_toc()
    
    # Print summary
    print("\n" + "="*70)
    print("CHUNKS SUMMARY")
    print("="*70)
    print(f"Total chunks: {len(chunks)}")
    by_type = {}
    for chunk in chunks:
        t = chunk.section_type.value
        by_type[t] = by_type.get(t, 0) + 1
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")
    
    # Save chunks and TOC
    output_file = "data/processed/easa_2018_1139_chunks.json"
    toc_file = "data/processed/easa_2018_1139_toc.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    parser.save_chunks(output_file)
    parser.save_toc(toc_file)
    
    print(f"\nOutput files:")
    print(f"  Chunks: {output_file}")
    print(f"  TOC: {toc_file}")


if __name__ == "__main__":
    main()