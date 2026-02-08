from unittest.mock import MagicMock

import pytest

import src.quiz_gen.agents.workflow as workflow_module
from src.quiz_gen.agents.config import AgentConfig


def build_workflow(tmp_path, monkeypatch):
    config = AgentConfig(
        openai_api_key="sk-openai-test",
        anthropic_api_key="sk-anthropic-test",
        output_directory=str(tmp_path),
        verbose=False,
    )

    conceptual = MagicMock()
    conceptual.model = "gpt-4o"
    practical = MagicMock()
    practical.model = "claude-sonnet-4-20250514"
    judge = MagicMock()
    validator = MagicMock()

    monkeypatch.setattr(workflow_module, "ConceptualGenerator", MagicMock(return_value=conceptual))
    monkeypatch.setattr(workflow_module, "PracticalGenerator", MagicMock(return_value=practical))
    monkeypatch.setattr(workflow_module, "Judge", MagicMock(return_value=judge))
    monkeypatch.setattr(workflow_module, "Validator", MagicMock(return_value=validator))

    return workflow_module.QuizGenerationWorkflow(config=config), conceptual, practical, judge, validator


@pytest.fixture
def sample_chunk():
    return {
        "title": "Aircraft Maintenance",
        "number": "2",
        "section_type": "article",
        "content": "Aircraft must be maintained according to the approved schedule.",
        "hierarchy_path": ["Regulation", "Chapter 2", "Article 2"],
    }


def test_validate_questions_collects_valid_only(tmp_path, monkeypatch, sample_chunk):
    workflow, _, _, _, validator = build_workflow(tmp_path, monkeypatch)

    validator.validate_batch.return_value = [
        {"valid": True, "score": 9, "issues": []},
        {"valid": False, "score": 5, "issues": ["Missing explanation"]},
    ]

    state = {
        "chunk": sample_chunk,
        "conceptual_qa": {"question": "Q1"},
        "practical_qa": {"question": "Q2"},
    }

    result = workflow._validate_questions(state)

    assert result["all_valid"] is False
    assert len(result["validation_results"]) == 2
    assert result["final_questions"] == [{"question": "Q1"}]
    assert result["current_step"] == "validate_questions"


def test_judge_questions_sets_metadata(tmp_path, monkeypatch, sample_chunk):
    workflow, conceptual, practical, judge, _ = build_workflow(tmp_path, monkeypatch)

    judge.judge.return_value = {
        "decision": "accept_both",
        "reasoning": "ok",
        "questions": [
            {"question": "Q1", "focus": "conceptual"},
            {"question": "Q2", "focus": "practical", "generator": "practical", "model": practical.model},
        ],
    }

    state = {
        "chunk": sample_chunk,
        "conceptual_qa": {"question": "Q1", "focus": "conceptual"},
        "practical_qa": {"question": "Q2", "focus": "practical"},
        "validation_results": [],
    }

    result = workflow._judge_questions(state)

    assert result["judge_decision"] == "accept_both"
    assert result["final_questions"][0]["generator"] == "conceptual"
    assert result["final_questions"][0]["model"] == conceptual.model
    assert result["final_questions"][1]["generator"] == "practical"
    assert result["final_questions"][1]["model"] == practical.model


def test_await_human_feedback_accepts_and_rejects(tmp_path, monkeypatch, sample_chunk):
    workflow, _, _, _, _ = build_workflow(tmp_path, monkeypatch)

    accepted = workflow._await_human_feedback({"all_valid": True})
    assert accepted["human_action"] == "accept"
    assert accepted["current_step"] == "await_human_feedback"

    rejected = workflow._await_human_feedback({"all_valid": False})
    assert rejected["human_action"] == "reject"


def test_route_after_human_feedback(tmp_path, monkeypatch):
    workflow, _, _, _, _ = build_workflow(tmp_path, monkeypatch)

    assert workflow._route_after_human_feedback({"human_action": "accept"}) == "accept"
    assert workflow._route_after_human_feedback({"human_action": "improve"}) == "improve"
    assert workflow._route_after_human_feedback({"human_action": "reject"}) == "reject"
    assert workflow._route_after_human_feedback({}) == "reject"


def test_save_result_writes_file(tmp_path, monkeypatch, sample_chunk):
    workflow, _, _, _, _ = build_workflow(tmp_path, monkeypatch)

    result = {
        "chunk": sample_chunk,
        "final_questions": [{"question": "Q1"}],
        "judge_decision": "accept_both",
        "validation_results": [{"valid": True, "score": 9, "issues": []}],
        "errors": [],
    }

    workflow._save_result(result, str(tmp_path))

    saved_path = tmp_path / "quiz_2.json"
    assert saved_path.exists()
    content = saved_path.read_text(encoding="utf-8")
    assert "\"questions\"" in content
    assert "Q1" in content


def test_run_invokes_app_with_thread_id(tmp_path, monkeypatch, sample_chunk):
    workflow, _, _, _, _ = build_workflow(tmp_path, monkeypatch)

    workflow.app = MagicMock()
    workflow.app.invoke.return_value = {"final_questions": []}

    result = workflow.run(sample_chunk)

    assert result == {"final_questions": []}
    args, _kwargs = workflow.app.invoke.call_args
    assert args[1]["configurable"]["thread_id"] == sample_chunk["number"]


def test_run_batch_saves_only_when_questions_present(tmp_path, monkeypatch, sample_chunk):
    workflow, _, _, _, _ = build_workflow(tmp_path, monkeypatch)

    chunks = [
        sample_chunk,
        {**sample_chunk, "number": "3", "title": "Aircraft Safety"},
    ]

    workflow.run = MagicMock(side_effect=[
        {"chunk": chunks[0], "final_questions": [{"question": "Q1"}]},
        {"chunk": chunks[1], "final_questions": []},
    ])
    workflow._save_result = MagicMock()

    results = workflow.run_batch(chunks, save_output=True, output_dir=str(tmp_path))

    assert len(results) == 2
    workflow._save_result.assert_called_once_with(results[0], str(tmp_path))
