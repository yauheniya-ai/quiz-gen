#!/usr/bin/env python3
"""
Example: Parsing EASA Regulation (EU) 2018/1139
Chunks the document into structured pieces with proper citations.

Note: Install the package first with: pip install -e .
"""

from pathlib import Path
from quiz_gen import EURLexParser


def main():
    """Parse and chunk the AI Act regulation document"""
    
    url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401689"
    
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
    output_file = "data/processed/aiact_2024_1689_chunks.json"
    toc_file = "data/processed/aiact_2024_1689_toc.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    parser.save_chunks(output_file)
    parser.save_toc(toc_file)
    
    print(f"\nOutput files:")
    print(f"  Chunks: {output_file}")
    print(f"  TOC: {toc_file}")


if __name__ == "__main__":
    main()