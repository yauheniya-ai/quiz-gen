import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console as RichConsole
from typer.testing import CliRunner

from quiz_gen import cli
from quiz_gen.cli import _get_default_filename, app

runner = CliRunner()

test_html_path = (
    Path(__file__).parent.parent.parent
    / "data/raw/2024_1689_Artificial Intelligence_Act.html"
).resolve()


def run_cli(*args):
    """Run the CLI and capture all output, including Rich console output.

    Rich's Console caches sys.stdout at import time, so we patch the module-level
    console with one that writes to a StringIO buffer we can inspect.
    """
    buf = StringIO()
    test_console = RichConsole(file=buf, highlight=False, width=120)
    with patch("quiz_gen.cli.console", test_console):
        result = runner.invoke(app, [str(a) for a in args])
    # buf holds Rich output; result.output holds any direct click/typer writes
    return result.exit_code, buf.getvalue() + (result.output or "")


# ── Parser tests ──────────────────────────────────────────────────────────────


def test_cli_print_stats_and_save(tmp_path):
    chunks_file = tmp_path / "test_chunks.json"
    toc_file = tmp_path / "test_toc.json"
    code, output = run_cli(
        "parse",
        str(test_html_path),
        "-o",
        str(tmp_path),
        "--chunks",
        "test_chunks.json",
        "--toc",
        "test_toc.json",
    )
    assert code == 0, output
    assert "Successfully parsed document" in output
    assert chunks_file.exists()
    assert toc_file.exists()


def test_cli_print_toc(tmp_path):
    code, output = run_cli(
        "parse", str(test_html_path), "-o", str(tmp_path), "--no-save", "--print-toc"
    )
    assert code == 0, output
    assert "TABLE OF CONTENTS" in output
    assert "Successfully parsed document" in output


def test_cli_no_save(tmp_path):
    code, output = run_cli(
        "parse", str(test_html_path), "-o", str(tmp_path), "--no-save"
    )
    assert code == 0, output
    files = list(tmp_path.glob("*.json"))
    assert not files


def test_cli_file_not_found(tmp_path):
    code, output = run_cli("parse", str(tmp_path / "notfound.html"))
    assert code == 1
    assert "File not found" in output


def test_cli_version():
    code, output = run_cli("--version")
    assert code == 0
    assert "quiz-gen" in output


def test_cli_verbose(tmp_path):
    code, output = run_cli(
        "parse",
        str(test_html_path),
        "-o",
        str(tmp_path),
        "--no-save",
        "--verbose",
    )
    assert code == 0, output
    assert "Parsing document..." in output or "Reading document from file:" in output


def test_cli_verbose_error_traceback(tmp_path):
    """Verbose mode should show error message."""
    code, output = run_cli("parse", str(tmp_path / "notfound.html"), "--verbose")
    assert code == 1
    assert "File not found" in output


def test_cli_url_verbose_exception_traceback(tmp_path):
    """URL + verbose + raised exception should report the error."""
    with patch(
        "quiz_gen.cli.EURLexParser", side_effect=RuntimeError("URL fetch failed")
    ):
        code, output = run_cli(
            "parse",
            "https://example.com/document.html",
            "-o",
            str(tmp_path),
            "--verbose",
            "--no-save",
        )
    assert code == 1
    assert "URL fetch failed" in output


def test_cli_no_input_shows_help():
    """No subcommand should print help (with 'serve' and 'parse') and exit 0."""
    code, output = run_cli()
    assert code == 0
    assert "serve" in output or "parse" in output


# ── _get_default_filename tests ───────────────────────────────────────────────


def test_get_default_filename_celex_url():
    url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139"
    result = _get_default_filename(url, "chunks")
    assert result == "32018R1139_chunks.json"


def test_get_default_filename_celex_url_with_ampersand():
    url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019R0945&from=EN"
    result = _get_default_filename(url, "toc")
    assert result == "32019R0945_toc.json"


def test_get_default_filename_non_celex_url():
    url = "https://example.com/document.html"
    result = _get_default_filename(url, "chunks")
    assert result == "document_chunks.json"


def test_get_default_filename_local_file():
    result = _get_default_filename("data/documents/regulation.html", "toc")
    assert result == "regulation_toc.json"


def test_get_default_filename_local_file_stem():
    result = _get_default_filename("/some/path/2024_1689_AI_Act.html", "chunks")
    assert result == "2024_1689_AI_Act_chunks.json"


# ── serve subcommand tests ────────────────────────────────────────────────────


def test_cli_serve_launches_server():
    """quiz-gen serve should call uvicorn.run with correct arguments."""
    mock_uvicorn = MagicMock()
    with patch("quiz_gen.cli._uvicorn", mock_uvicorn):
        code, output = run_cli("serve", "--no-browser")
    assert "Starting quiz-gen UI" in output
    mock_uvicorn.run.assert_called_once()


def test_cli_serve_custom_port():
    """quiz-gen serve --port 9000 should pass port=9000 to uvicorn."""
    mock_uvicorn = MagicMock()
    with patch("quiz_gen.cli._uvicorn", mock_uvicorn):
        code, output = run_cli("serve", "--port", "9000", "--no-browser")
    assert "9000" in output
    assert mock_uvicorn.run.call_args.kwargs.get("port") == 9000


def test_serve_missing_uvicorn():
    """serve should print error and exit 1 if uvicorn is not installed."""
    with patch("quiz_gen.cli._uvicorn", None):
        code, output = run_cli("serve")
    assert code == 1
    assert "uvicorn" in output


def test_serve_no_browser_flag():
    """serve --no-browser should not open a browser."""
    mock_uvicorn = MagicMock()
    mock_browser = MagicMock()
    with patch("quiz_gen.cli._uvicorn", mock_uvicorn):
        with patch("webbrowser.open", mock_browser):
            run_cli("serve", "--no-browser")
    mock_browser.assert_not_called()


def test_serve_open_browser():
    """serve without --no-browser should call webbrowser.open with the correct URL."""
    import threading

    mock_uvicorn = MagicMock()
    mock_browser = MagicMock()
    opened_event = threading.Event()

    def fake_open(url):
        mock_browser(url)
        opened_event.set()

    with patch("quiz_gen.cli._uvicorn", mock_uvicorn):
        with patch("webbrowser.open", fake_open):
            with patch("time.sleep"):  # skip the 1.5 s delay
                run_cli("serve")
    opened_event.wait(timeout=2)
    mock_browser.assert_called_once_with("http://localhost:8000")


def test_serve_log_level_flag():
    """serve --log-level debug should pass log_level=debug to uvicorn."""
    mock_uvicorn = MagicMock()
    with patch("quiz_gen.cli._uvicorn", mock_uvicorn):
        run_cli("serve", "--log-level", "debug", "--no-browser")
    assert mock_uvicorn.run.call_args.kwargs["log_level"] == "debug"


def test_serve_reload_flag():
    """serve --reload should pass reload=True to uvicorn."""
    mock_uvicorn = MagicMock()
    with patch("quiz_gen.cli._uvicorn", mock_uvicorn):
        run_cli("serve", "--reload", "--no-browser")
    assert mock_uvicorn.run.call_args.kwargs["reload"] is True
