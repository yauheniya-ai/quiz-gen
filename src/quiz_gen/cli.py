#!/usr/bin/env python3
"""
Command-line interface for quiz-gen package.
Parse EUR-Lex documents and extract structured content.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from quiz_gen.__version__ import __version__
from quiz_gen.parsers.html.eu_lex_parser import EURLexParser


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="quiz-gen",
        description="Parse EUR-Lex regulatory documents and extract structured content into chunks and TOC.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse from URL
  quiz-gen https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139
  
  # Parse local HTML file
  quiz-gen data/documents/html/regulation.html
  
  # Specify output directory
  quiz-gen --output data/output regulation.html
  
  # Specify custom output filenames
  quiz-gen --chunks my_chunks.json --toc my_toc.json regulation.html
  
  # Print TOC to console
  quiz-gen --print-toc regulation.html
        """
    )
    
    parser.add_argument(
        "input",
        help="URL or path to local HTML file of EUR-Lex document"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="data/processed",
        help="Output directory for generated files (default: data/processed)"
    )
    
    parser.add_argument(
        "--chunks",
        type=str,
        help="Custom filename for chunks JSON (default: <input>_chunks.json)"
    )
    
    parser.add_argument(
        "--toc",
        type=str,
        help="Custom filename for TOC JSON (default: <input>_toc.json)"
    )
    
    parser.add_argument(
        "--print-toc",
        action="store_true",
        help="Print formatted table of contents to console"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save output files, only display stats"
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser


def get_default_filename(input_path: str, suffix: str) -> str:
    """Generate default filename from input path or URL."""
    # Extract document identifier from URL or filename
    if input_path.startswith("http"):
        # Extract CELEX number from URL
        if "CELEX:" in input_path or "CELEX%3A" in input_path:
            celex = input_path.split("CELEX")[-1].split(":")[1] if ":" in input_path else input_path.split("%3A")[1]
            celex = celex.split("&")[0].split("?")[0]
            return f"{celex}_{suffix}.json"
        return f"document_{suffix}.json"
    else:
        # Use filename without extension
        stem = Path(input_path).stem
        # Remove URL encoding if present
        stem = stem.replace("%3A", "_").replace("%3A", "_")
        return f"{stem}_{suffix}.json"


def parse_document(
    input_source: str,
    output_dir: str,
    chunks_filename: Optional[str] = None,
    toc_filename: Optional[str] = None,
    print_toc: bool = False,
    no_save: bool = False,
    verbose: bool = False
) -> int:
    """
    Parse EUR-Lex document and save results.
    
    Returns:
        0 on success, 1 on error
    """
    try:
        # Determine if input is URL or file
        if input_source.startswith("http://") or input_source.startswith("https://"):
            if verbose:
                print(f"Fetching document from URL: {input_source}")
            parser = EURLexParser(url=input_source)
        else:
            input_path = Path(input_source)
            if not input_path.exists():
                print(f"Error: File not found: {input_source}", file=sys.stderr)
                return 1
            
            if verbose:
                print(f"Reading document from file: {input_source}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            parser = EURLexParser(html_content=html_content)
        
        # Parse document
        if verbose:
            print("Parsing document...")
        chunks, toc = parser.parse()
        
        # Print statistics
        print(f"\n✓ Successfully parsed document")
        print(f"  Title: {toc.get('title', 'Unknown')[:80]}...")
        print(f"  Total chunks: {len(chunks)}")
        
        # Count by type
        from collections import Counter
        types = Counter(c.section_type.value for c in chunks)
        for section_type, count in sorted(types.items()):
            print(f"    {section_type}: {count}")
        
        # Print TOC if requested
        if print_toc:
            parser.print_toc()
        
        # Save files unless --no-save
        if not no_save:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Determine output filenames
            chunks_file = chunks_filename or get_default_filename(input_source, "chunks")
            toc_file = toc_filename or get_default_filename(input_source, "toc")
            
            chunks_path = output_path / chunks_file
            toc_path = output_path / toc_file
            
            # Save files
            parser.save_chunks(str(chunks_path))
            parser.save_toc(str(toc_path))
            
            print(f"\n✓ Files saved to: {output_dir}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def main() -> int:
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    return parse_document(
        input_source=args.input,
        output_dir=args.output,
        chunks_filename=args.chunks,
        toc_filename=args.toc,
        print_toc=args.print_toc,
        no_save=args.no_save,
        verbose=args.verbose
    )


if __name__ == "__main__":
    sys.exit(main())
