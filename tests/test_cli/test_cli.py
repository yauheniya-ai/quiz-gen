
import sys
from pathlib import Path

import pytest

from quiz_gen import cli

test_html_path = (Path(__file__).parent.parent.parent / 'data/raw/2024_1689_Artificial Intelligence_Act.html').resolve()

def run_cli_with_args(args, monkeypatch, capsys):
    """Run the CLI in-process, return (exit_code, stdout+stderr)."""
    monkeypatch.setattr(sys, "argv", ["quiz-gen"] + [str(a) for a in args])
    try:
        code = cli.main()
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    captured = capsys.readouterr()
    return code, captured.out + captured.err

def test_cli_print_stats_and_save(tmp_path, monkeypatch, capsys):
    outdir = tmp_path
    chunks_file = outdir / 'test_chunks.json'
    toc_file = outdir / 'test_toc.json'
    args = [str(test_html_path), '-o', str(outdir), '--chunks', 'test_chunks.json', '--toc', 'test_toc.json']
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 0, output
    assert 'Successfully parsed document' in output
    assert chunks_file.exists()
    assert toc_file.exists()

def test_cli_print_toc(tmp_path, monkeypatch, capsys):
    args = [str(test_html_path), '-o', str(tmp_path), '--no-save', '--print-toc']
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 0, output
    assert 'TABLE OF CONTENTS' in output
    assert 'Successfully parsed document' in output

def test_cli_no_save(tmp_path, monkeypatch, capsys):
    args = [str(test_html_path), '-o', str(tmp_path), '--no-save']
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 0, output
    files = list(tmp_path.glob('*.json'))
    assert not files

def test_cli_file_not_found(tmp_path, monkeypatch, capsys):
    args = [str(tmp_path / 'notfound.html')]
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 1
    assert 'File not found' in output

def test_cli_version(monkeypatch, capsys):
    args = ['--version']
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 0
    assert 'quiz-gen' in output

def test_cli_verbose(tmp_path, monkeypatch, capsys):
    args = [str(test_html_path), '-o', str(tmp_path), '--no-save', '--verbose']
    code, output = run_cli_with_args(args, monkeypatch, capsys)
    assert code == 0, output
    assert 'Parsing document...' in output or 'Reading document from file:' in output

# Note: test_cli_url is omitted here because URL-based tests should avoid network calls.
