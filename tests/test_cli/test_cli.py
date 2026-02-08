
import os
import sys
import subprocess
import pytest
from pathlib import Path

test_html_path = (Path(__file__).parent.parent.parent / 'data/raw/2024_1689_Artificial Intelligence_Act.html').resolve()

def run_cli_with_args(args):
    """Run the CLI as a module in a subprocess, return (exit_code, stdout+stderr)."""
    cmd = [sys.executable, '-m', 'quiz_gen.cli'] + [str(a) for a in args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr

def test_cli_print_stats_and_save(tmp_path):
    outdir = tmp_path
    chunks_file = outdir / 'test_chunks.json'
    toc_file = outdir / 'test_toc.json'
    args = [str(test_html_path), '-o', str(outdir), '--chunks', 'test_chunks.json', '--toc', 'test_toc.json']
    code, output = run_cli_with_args(args)
    assert code == 0, output
    assert 'Successfully parsed document' in output
    assert chunks_file.exists()
    assert toc_file.exists()

def test_cli_print_toc(tmp_path):
    args = [str(test_html_path), '-o', str(tmp_path), '--no-save', '--print-toc']
    code, output = run_cli_with_args(args)
    assert code == 0, output
    assert 'TABLE OF CONTENTS' in output
    assert 'Successfully parsed document' in output

def test_cli_no_save(tmp_path):
    args = [str(test_html_path), '-o', str(tmp_path), '--no-save']
    code, output = run_cli_with_args(args)
    assert code == 0, output
    files = list(tmp_path.glob('*.json'))
    assert not files

def test_cli_file_not_found(tmp_path):
    args = [str(tmp_path / 'notfound.html')]
    code, output = run_cli_with_args(args)
    assert code == 1
    assert 'File not found' in output

def test_cli_version():
    args = ['--version']
    code, output = run_cli_with_args(args)
    assert code == 0
    assert 'quiz-gen' in output

def test_cli_verbose(tmp_path):
    args = [str(test_html_path), '-o', str(tmp_path), '--no-save', '--verbose']
    code, output = run_cli_with_args(args)
    assert code == 0, output
    assert 'Parsing document...' in output or 'Reading document from file:' in output

# Note: test_cli_url is omitted here because subprocess-based CLI tests cannot easily monkeypatch internals.
