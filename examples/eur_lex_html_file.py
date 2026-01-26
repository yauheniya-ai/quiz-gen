#!/usr/bin/env python3
"""
Parsing EU-Lex Regulation
Chunks the document into structured pieces with proper citations.
"""

from pathlib import Path
from quiz_gen import EURLexParser


def main():
    """Parse and chunk the EU-Lex HTML document"""
    
    #url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019R0945"
    html_file = "data/documents/html/2018_1139_Common_Rules_Civil_Aviation.html"
    doc_id = "2018_1139"

    print(f"Parsing: {html_file}\n")
    
    # Read the HTML content from file
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse document - returns (chunks, toc)
    parser = EURLexParser(html_content=html_content)
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
    output_file = f"data/processed/{doc_id}_chunks.json"
    toc_file = f"data/processed/{doc_id}_toc.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    parser.save_chunks(output_file)
    parser.save_toc(toc_file)
    
    print(f"\nOutput files:")
    print(f"  Chunks: {output_file}")
    print(f"  TOC: {toc_file}")


if __name__ == "__main__":
    main()