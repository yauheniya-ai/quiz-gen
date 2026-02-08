import json
from pathlib import Path

import pytest

from src.quiz_gen.agents.config import AgentConfig


def test_config_loads_env_and_creates_output_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-anthropic-test")
    monkeypatch.setenv("OPENAI_API_BASE", "https://openai.test")
    monkeypatch.setenv("ANTHROPIC_API_BASE", "https://anthropic.test")

    out_dir = tmp_path / "out"
    config = AgentConfig(output_directory=str(out_dir), verbose=False)

    assert config.openai_api_key == "sk-openai-test"
    assert config.anthropic_api_key == "sk-anthropic-test"
    assert config.openai_api_base == "https://openai.test"
    assert config.anthropic_api_base == "https://anthropic.test"
    assert out_dir.exists()

    masked = config.to_dict()
    assert masked["openai_api_key"] == "***"
    assert masked["anthropic_api_key"] == "***"


def test_validate_reports_multiple_errors(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    config = AgentConfig(
        openai_api_key=None,
        anthropic_api_key=None,
        openai_api_base=None,
        anthropic_api_base=None,
        conceptual_model="not-a-model",
        validator_model="also-bad",
        min_validation_score=11,
        output_directory=str(tmp_path),
        verbose=False,
    )

    with pytest.raises(ValueError) as exc:
        config.validate()

    message = str(exc.value)
    assert "OPENAI_API_KEY is required for provider 'openai'" in message
    assert "ANTHROPIC_API_KEY is required for provider 'anthropic'" in message
    assert "min_validation_score must be between 0 and 10" in message


def test_save_and_load_masks_api_keys(tmp_path):
    config = AgentConfig(
        openai_api_key="sk-open",
        anthropic_api_key="sk-anth",
        output_directory=str(tmp_path),
        verbose=False,
    )

    config_path = tmp_path / "config.json"
    config.save(str(config_path))

    saved = json.loads(Path(config_path).read_text(encoding="utf-8"))
    assert saved["openai_api_key"] == "***"
    assert saved["anthropic_api_key"] == "***"

    loaded = AgentConfig.load(str(config_path))
    assert loaded.openai_api_key == "***"
    assert loaded.anthropic_api_key == "***"
    assert loaded.output_directory == str(tmp_path)


def test_from_env_file_reads_keys(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_API_KEY=sk-openai-from-file\n"
        "ANTHROPIC_API_KEY=sk-anthropic-from-file\n"
        "OPENAI_API_BASE=https://openai.file\n"
        "ANTHROPIC_API_BASE=https://anthropic.file\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_BASE", raising=False)
    monkeypatch.chdir(tmp_path)
    config = AgentConfig.from_env_file(str(env_file))

    assert config.openai_api_key == "sk-openai-from-file"
    assert config.anthropic_api_key == "sk-anthropic-from-file"
    assert config.openai_api_base == "https://openai.file"
    assert config.anthropic_api_base == "https://anthropic.file"
    assert (tmp_path / "data" / "quizzes").exists()


def test_print_summary_outputs_status(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = AgentConfig(
        openai_api_key="sk-open",
        anthropic_api_key=None,
        output_directory=str(tmp_path),
        verbose=False,
    )

    config.print_summary()
    output = capsys.readouterr().out

    assert "Agent Configuration Summary" in output
    assert "OpenAI API Key: ✓ Set" in output
    assert "Anthropic API Key: ✗ Missing" in output
    assert "Conceptual Generator" in output
