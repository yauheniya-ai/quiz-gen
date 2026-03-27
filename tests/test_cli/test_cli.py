import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from quiz_gen import cli
from quiz_gen.cli import get_default_filename, launch_ui

test_html_path = (
    Path(__file__).parent.parent.parent
    / "data/raw/2024_1689_Artificial Intelligence_Act.html"
).resolve()


def run_cli_with_args(args, monkeypatch, capsys):
    """Run the CLI in-process, return (exit_code, stdout+stderr)."""
    monkeypatch.setattr(sys, "argv", ["quiz-gen"] + [str(a) for a in args])
    try:
        code = cli.main()
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    captured = capsys.readouterr()
    return code, captured.out + captured.err


# ── Parser tests ──────────────────────────────────────────────────────────────


def test_cli_print_stats_and_save(tmp_path, monkeypatch, capsys):
    outdir = tmp_path
    chunks_file = outdir / "test_chunks.json"
    toc_file = outdir / "test_toc.json"
    args = [
        str(test_html_path),
        "-o",
        str(outdir),
        "--chunks",
        "test_chunks.json",
        "--toc",
        "test_toc.json",
    ]
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 0, output
    assert "Successfully parsed document" in output
    assert chunks_file.exists()
    assert toc_file.exists()


def test_cli_print_toc(tmp_path, monkeypatch, capsys):
    args = [str(test_html_path), "-o", str(tmp_path), "--no-save", "--print-toc"]
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 0, output
    assert "TABLE OF CONTENTS" in output
    assert "Successfully parsed document" in output


def test_cli_no_save(tmp_path, monkeypatch, capsys):
    args = [str(test_html_path), "-o", str(tmp_path), "--no-save"]
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 0, output
    files = list(tmp_path.glob("*.json"))
    assert not files


def test_cli_file_not_found(tmp_path, monkeypatch, capsys):
    args = [str(tmp_path / "notfound.html")]
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 1
    assert "File not found" in output


def test_cli_version(monkeypatch, capsys):
    args = ["--version"]
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 0
    assert "quiz-gen" in output


def test_cli_verbose(tmp_path, monkeypatch, capsys):
    args = [str(test_html_path), "-o", str(tmp_path), "--no-save", "--verbose"]
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 0, output
    assert "Parsing document..." in output or "Reading document from file:" in output


def test_cli_verbose_error_traceback(tmp_path, monkeypatch, capsys):
    """Verbose mode should print traceback on error."""
    args = [str(tmp_path / "notfound.html"), "--verbose"]
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 1
    assert "File not found" in output


def test_cli_url_verbose_exception_traceback(tmp_path, monkeypatch, capsys):
    """Lines 219-221 (URL + verbose) and 278-284 (except Exception + verbose traceback).

    EURLexParser raises so we travel: verbose print → parser init → except block → traceback.
    """
    with patch(
        "quiz_gen.cli.EURLexParser", side_effect=RuntimeError("URL fetch failed")
    ):
        args = [
            "https://example.com/document.html",
            "-o",
            str(tmp_path),
            "--verbose",
            "--no-save",
        ]
        code, output = run_cli_with_args(args, monkeypatch, capsys)

    assert code == 1
    assert "URL fetch failed" in output


def test_cli_no_input_no_ui(monkeypatch, capsys):
    """No input and no --ui should print help and return 1."""
    monkeypatch.setattr(sys, "argv", ["quiz-gen"])
    try:
        code = cli.main()
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    captured = capsys.readouterr()
    assert code == 1
    assert "usage" in (captured.out + captured.err).lower()


# ── get_default_filename tests ────────────────────────────────────────────────


def test_get_default_filename_celex_url():
    url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32018R1139"
    result = get_default_filename(url, "chunks")
    assert result == "32018R1139_chunks.json"


def test_get_default_filename_celex_url_with_ampersand():
    url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019R0945&from=EN"
    result = get_default_filename(url, "toc")
    assert result == "32019R0945_toc.json"


def test_get_default_filename_non_celex_url():
    url = "https://example.com/document.html"
    result = get_default_filename(url, "chunks")
    assert result == "document_chunks.json"


def test_get_default_filename_local_file():
    result = get_default_filename("data/documents/regulation.html", "toc")
    assert result == "regulation_toc.json"


def test_get_default_filename_local_file_stem():
    result = get_default_filename("/some/path/2024_1689_AI_Act.html", "chunks")
    assert result == "2024_1689_AI_Act_chunks.json"


# ── --ui flag tests ───────────────────────────────────────────────────────────


def test_cli_ui_launches_server(monkeypatch, capsys):
    """--ui should call uvicorn.run with correct arguments."""
    mock_uvicorn = MagicMock()
    monkeypatch.setattr("quiz_gen.cli._uvicorn", mock_uvicorn)
    monkeypatch.setattr(sys, "argv", ["quiz-gen", "--ui"])
    try:
        cli.main()
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "Starting quiz-gen UI" in captured.out
    mock_uvicorn.run.assert_called_once()


def test_cli_ui_custom_port(monkeypatch, capsys):
    """--ui --port 9000 should pass port=9000 to uvicorn."""
    mock_uvicorn = MagicMock()
    monkeypatch.setattr("quiz_gen.cli._uvicorn", mock_uvicorn)
    monkeypatch.setattr(sys, "argv", ["quiz-gen", "--ui", "--port", "9000"])
    try:
        cli.main()
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "9000" in captured.out
    _, kwargs = mock_uvicorn.run.call_args
    assert (
        kwargs.get("port") == 9000
        or mock_uvicorn.run.call_args[0][1] == 9000
        or 9000 in mock_uvicorn.run.call_args.args
        or mock_uvicorn.run.call_args.kwargs.get("port") == 9000
    )


def test_launch_ui_missing_uvicorn(monkeypatch, capsys):
    """launch_ui should return 1 and print error if uvicorn is not installed."""
    monkeypatch.setattr("quiz_gen.cli._uvicorn", None)
    code = launch_ui()
    captured = capsys.readouterr()
    assert code == 1
    assert "uvicorn" in captured.err


def test_launch_ui_success(monkeypatch):
    """launch_ui should call uvicorn.run and return 0."""
    mock_uvicorn = MagicMock()
    monkeypatch.setattr("quiz_gen.cli._uvicorn", mock_uvicorn)
    code = launch_ui(host="127.0.0.1", port=8000, open_browser=False)
    assert code == 0
    mock_uvicorn.run.assert_called_once_with(
        "quiz_gen.ui.server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="warning",
    )


def test_launch_ui_reload(monkeypatch):
    """launch_ui with reload=True should pass reload=True to uvicorn."""
    mock_uvicorn = MagicMock()
    monkeypatch.setattr("quiz_gen.cli._uvicorn", mock_uvicorn)
    code = launch_ui(host="0.0.0.0", port=8000, reload=True, open_browser=False)
    assert code == 0
    mock_uvicorn.run.assert_called_once_with(
        "quiz_gen.ui.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="warning",
    )


def test_launch_ui_no_browser(monkeypatch):
    """open_browser=False should not call webbrowser.open."""
    mock_uvicorn = MagicMock()
    mock_browser = MagicMock()
    monkeypatch.setattr("quiz_gen.cli._uvicorn", mock_uvicorn)
    with patch("webbrowser.open", mock_browser):
        launch_ui(open_browser=False)
    mock_browser.assert_not_called()


def test_launch_ui_open_browser(monkeypatch):
    """open_browser=True should call webbrowser.open with the correct URL via a background thread."""
    import threading

    mock_uvicorn = MagicMock()
    mock_browser = MagicMock()
    opened_event = threading.Event()

    def fake_open(url):
        mock_browser(url)
        opened_event.set()

    monkeypatch.setattr("quiz_gen.cli._uvicorn", mock_uvicorn)
    with patch("webbrowser.open", fake_open):
        with patch("time.sleep"):  # skip the 1.5s delay
            launch_ui(port=8000, open_browser=True)
    opened_event.wait(timeout=2)
    mock_browser.assert_called_once_with("http://localhost:8000")


def test_launch_ui_log_level(monkeypatch):
    """log_level should be passed to uvicorn.run."""
    mock_uvicorn = MagicMock()
    monkeypatch.setattr("quiz_gen.cli._uvicorn", mock_uvicorn)
    launch_ui(open_browser=False, log_level="debug")
    _, kwargs = mock_uvicorn.run.call_args
    assert kwargs["log_level"] == "debug"


def test_cli_ui_no_browser_flag(monkeypatch, capsys):
    """--ui --no-browser should not open a browser."""
    mock_uvicorn = MagicMock()
    mock_browser = MagicMock()
    monkeypatch.setattr("quiz_gen.cli._uvicorn", mock_uvicorn)
    monkeypatch.setattr(sys, "argv", ["quiz-gen", "--ui", "--no-browser"])
    with patch("webbrowser.open", mock_browser):
        try:
            cli.main()
        except SystemExit:
            pass
    mock_browser.assert_not_called()


def test_cli_ui_log_level_flag(monkeypatch):
    """--ui --log-level debug should pass log_level=debug to uvicorn."""
    mock_uvicorn = MagicMock()
    monkeypatch.setattr("quiz_gen.cli._uvicorn", mock_uvicorn)
    monkeypatch.setattr(
        sys, "argv", ["quiz-gen", "--ui", "--log-level", "debug", "--no-browser"]
    )
    with patch("webbrowser.open"):
        try:
            cli.main()
        except SystemExit:
            pass
    _, kwargs = mock_uvicorn.run.call_args
    assert kwargs["log_level"] == "debug"
