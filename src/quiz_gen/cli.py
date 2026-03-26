#!/usr/bin/env python3
"""
quiz-gen CLI
~~~~~~~~~~~~~
Command-line interface for the quiz-gen package.

Entry point registered in pyproject.toml::

    [project.scripts]
    quiz-gen = "quiz_gen.cli:main"

Usage examples
--------------
    quiz-gen --version

    # Launch the interactive web UI
    quiz-gen --ui

    # Launch on a custom port without opening a browser
    quiz-gen --ui --port 9000 --no-browser

    # Parse a document from URL
    quiz-gen https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139

    # Parse a local HTML file and print the TOC
    quiz-gen data/documents/html/regulation.html --print-toc

    # Save to a custom output directory with custom filenames
    quiz-gen regulation.html --output data/output --chunks my_chunks.json --toc my_toc.json
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    import uvicorn as _uvicorn
except ImportError:
    _uvicorn = None

from quiz_gen.__version__ import __version__
from quiz_gen.parsers.html.eur_lex_parser import EURLexParser


def launch_ui(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    open_browser: bool = True,
    log_level: str = "warning",
) -> int:
    """Launch the quiz-gen web UI using uvicorn."""
    if _uvicorn is None:
        print(
            "Error: uvicorn is required to launch the UI. Install it with: pip install uvicorn",
            file=sys.stderr,
        )
        return 1
    url = f"http://localhost:{port}"
    print(f"Starting quiz-gen UI at {url}")
    if open_browser:
        import webbrowser
        webbrowser.open(url)
    _uvicorn.run(
        "quiz_gen.ui.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )
    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="quiz-gen",
        description="AI-powered quiz generator for EUR-Lex regulatory documents.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # -- General ----------------------------------------------------------
    parser.add_argument(
        "input",
        nargs="?",
        help="URL or path to a local HTML file of an EUR-Lex document (not required with --ui)",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    # -- Document parsing -------------------------------------------------
    parse_group = parser.add_argument_group("Document parsing")
    parse_group.add_argument(
        "-o", "--output",
        type=str,
        default="data/processed",
        metavar="DIR",
        help="Output directory for generated files",
    )
    parse_group.add_argument(
        "--chunks",
        type=str,
        metavar="FILE",
        help="Custom filename for chunks JSON (default: <input>_chunks.json)",
    )
    parse_group.add_argument(
        "--toc",
        type=str,
        metavar="FILE",
        help="Custom filename for TOC JSON (default: <input>_toc.json)",
    )
    parse_group.add_argument(
        "--print-toc",
        action="store_true",
        help="Print formatted table of contents to console",
    )
    parse_group.add_argument(
        "--no-save",
        action="store_true",
        help="Skip saving output files, only display stats",
    )

    # -- Web UI -----------------------------------------------------------
    ui_group = parser.add_argument_group("Web UI")
    ui_group.add_argument(
        "--ui",
        action="store_true",
        help="Launch the interactive web UI",
    )
    ui_group.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        metavar="HOST",
        help="Host to bind the UI server to",
    )
    ui_group.add_argument(
        "--port",
        type=int,
        default=8000,
        metavar="PORT",
        help="Port to run the UI server on",
    )
    ui_group.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open a browser tab when starting the UI",
    )
    ui_group.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for the UI server (development mode)",
    )
    ui_group.add_argument(
        "--log-level",
        default="warning",
        choices=["debug", "info", "warning", "error"],
        metavar="LEVEL",
        help="Log level for the UI server: debug, info, warning, error",
    )

    return parser


def get_default_filename(input_path: str, suffix: str) -> str:
    """Generate default filename from input path or URL."""
    # Extract document identifier from URL or filename
    if input_path.startswith("http"):
        # Extract CELEX number from URL
        if "CELEX:" in input_path or "CELEX%3A" in input_path:
            celex = (
                input_path.split("CELEX")[-1].split(":")[1]
                if ":" in input_path
                else input_path.split("%3A")[1]
            )
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
    verbose: bool = False,
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

            with open(input_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            parser = EURLexParser(html_content=html_content)

        # Parse document
        if verbose:
            print("Parsing document...")
        chunks, toc = parser.parse()

        # Print statistics
        print("\n✓ Successfully parsed document")
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
            chunks_file = chunks_filename or get_default_filename(
                input_source, "chunks"
            )
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

    if args.ui:
        return launch_ui(
            host=args.host,
            port=args.port,
            reload=args.reload,
            open_browser=not args.no_browser,
            log_level=args.log_level,
        )

    if not args.input:
        parser.print_help()
        return 1

    return parse_document(
        input_source=args.input,
        output_dir=args.output,
        chunks_filename=args.chunks,
        toc_filename=args.toc,
        print_toc=args.print_toc,
        no_save=args.no_save,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    sys.exit(main())
