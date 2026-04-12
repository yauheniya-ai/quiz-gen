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
    quiz-gen serve

    # Launch on a custom port without opening a browser
    quiz-gen serve --port 9000 --no-browser

    # Parse a document from URL
    quiz-gen parse https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139

    # Parse a local HTML file and print the TOC
    quiz-gen parse data/documents/html/regulation.html --print-toc

    # Save to a custom output directory with custom filenames
    quiz-gen parse regulation.html --output data/output --chunks my_chunks.json --toc my_toc.json
"""

import sys
from collections import Counter
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.text import Text

try:
    import uvicorn as _uvicorn
except ImportError:
    _uvicorn = None

from quiz_gen.__version__ import __version__
from quiz_gen.parsers.html.eur_lex_parser import EURLexParser

console = Console()

# Tailwind blue-500
BLUE = "#3b82f6"

ASCII_ART = r"""              _                           
   __ _ _   _(_)____      __ _  ___ _ __  
  / _` | | | | |_  /____ / _` |/ _ \ '_ \ 
 | (_| | |_| | |/ /_____| (_| |  __/ | | |
  \__, |\__,_|_/___|     \__, |\___|_| |_|
     |_|                 |___/            """


def print_banner() -> None:
    """Print the quiz-gen ASCII art banner in blue."""
    console.print(Text(ASCII_ART, style=BLUE))
    console.print()


app = typer.Typer(
    name="quiz-gen",
    help="AI-powered quiz generator for EUR-Lex regulatory documents.",
    add_completion=False,
    rich_markup_mode="rich",
)



@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit."
    ),
) -> None:
    """AI-powered quiz generator for EUR-Lex regulatory documents."""
    print_banner()

    if version:
        console.print(f"[{BLUE}]quiz-gen[/{BLUE}] [bold]{__version__}[/bold]")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


# ---------------------------------------------------------------------------
# serve
# ---------------------------------------------------------------------------


@app.command("serve")
def serve_cmd(
    host: str = typer.Option(
        "0.0.0.0", "--host", help="Host to bind the server to.", metavar="HOST"
    ),
    port: int = typer.Option(
        8000, "--port", help="Port to run the server on.", metavar="PORT"
    ),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Do not open a browser tab on start."
    ),
    reload: bool = typer.Option(
        False, "--reload", help="Enable auto-reload (development mode)."
    ),
    log_level: str = typer.Option(
        "warning",
        "--log-level",
        help="Log level for the server: debug, info, warning, error.",
        metavar="LEVEL",
    ),
) -> None:
    """Launch the interactive web UI."""
    if _uvicorn is None:
        console.print(
            "[red]Error:[/red] uvicorn is required. "
            "Install it with: [bold]pip install uvicorn[/bold]"
        )
        raise typer.Exit(1)

    url = f"http://localhost:{port}"
    console.print(f"[{BLUE}]Starting quiz-gen UI at[/{BLUE}] [bold]{url}[/bold]")

    if not no_browser:
        import threading
        import webbrowser

        def _open() -> None:
            import time

            time.sleep(1.5)
            webbrowser.open(url)

        threading.Thread(target=_open, daemon=True).start()

    _uvicorn.run(
        "quiz_gen.ui.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------


@app.command("parse")
def parse_cmd(
    input: str = typer.Argument(
        ..., help="URL or path to a local HTML file of an EUR-Lex document."
    ),
    output: str = typer.Option(
        "data/processed",
        "--output",
        "-o",
        help="Output directory for generated files.",
        metavar="DIR",
    ),
    chunks: Optional[str] = typer.Option(
        None,
        "--chunks",
        help="Custom filename for chunks JSON (default: <input>_chunks.json).",
        metavar="FILE",
    ),
    toc: Optional[str] = typer.Option(
        None,
        "--toc",
        help="Custom filename for TOC JSON (default: <input>_toc.json).",
        metavar="FILE",
    ),
    print_toc: bool = typer.Option(
        False, "--print-toc", help="Print formatted table of contents to console."
    ),
    no_save: bool = typer.Option(
        False, "--no-save", help="Skip saving output files, only display stats."
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
) -> None:
    """Parse an EUR-Lex document and save chunks/TOC as JSON."""
    rc = _parse_document(
        input_source=input,
        output_dir=output,
        chunks_filename=chunks,
        toc_filename=toc,
        print_toc=print_toc,
        no_save=no_save,
        verbose=verbose,
    )
    raise typer.Exit(rc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_default_filename(input_path: str, suffix: str) -> str:
    """Generate a default JSON filename from an input URL or file path."""
    if input_path.startswith("http"):
        if "CELEX:" in input_path or "CELEX%3A" in input_path:
            celex = (
                input_path.split("CELEX")[-1].split(":")[1]
                if ":" in input_path
                else input_path.split("%3A")[1]
            )
            celex = celex.split("&")[0].split("?")[0]
            return f"{celex}_{suffix}.json"
        return f"document_{suffix}.json"

    stem = Path(input_path).stem.replace("%3A", "_")
    return f"{stem}_{suffix}.json"


def _parse_document(
    input_source: str,
    output_dir: str,
    chunks_filename: Optional[str] = None,
    toc_filename: Optional[str] = None,
    print_toc: bool = False,
    no_save: bool = False,
    verbose: bool = False,
) -> int:
    """Parse an EUR-Lex document and save results. Returns 0 on success, 1 on error."""
    try:
        if input_source.startswith("http://") or input_source.startswith("https://"):
            if verbose:
                console.print(f"Fetching document from URL: {input_source}")
            parser = EURLexParser(url=input_source)
        else:
            input_path = Path(input_source)
            if not input_path.exists():
                console.print(f"[red]Error:[/red] File not found: {input_source}")
                return 1
            if verbose:
                console.print(f"Reading document from file: {input_source}")
            with open(input_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            parser = EURLexParser(html_content=html_content)

        if verbose:
            console.print("Parsing document...")

        chunks, toc_data = parser.parse()

        console.print(f"\n[{BLUE}]✓[/{BLUE}] Successfully parsed document")
        console.print(
            f"  [dim]Title:[/dim] {toc_data.get('title', 'Unknown')[:80]}..."
        )
        console.print(f"  [dim]Total chunks:[/dim] {len(chunks)}")

        types = Counter(c.section_type.value for c in chunks)
        for section_type, count in sorted(types.items()):
            console.print(f"    {section_type}: {count}")

        if print_toc:
            parser.print_toc()

        if not no_save:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            chunks_file = chunks_filename or _get_default_filename(
                input_source, "chunks"
            )
            toc_file = toc_filename or _get_default_filename(input_source, "toc")

            parser.save_chunks(str(output_path / chunks_file))
            parser.save_toc(str(output_path / toc_file))

            console.print(f"\n[{BLUE}]✓[/{BLUE}] Files saved to: {output_dir}")

        return 0

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        return 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Main entry point registered in pyproject.toml."""
    app()


if __name__ == "__main__":
    main()
