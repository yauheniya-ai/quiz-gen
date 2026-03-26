from unittest.mock import MagicMock

import pytest

import src.quiz_gen.agents.workflow as workflow_module
from src.quiz_gen.agents.config import AgentConfig


def build_workflow(tmp_path, monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_BASE", raising=False)
    monkeypatch.delenv("GEMINI_API_BASE", raising=False)
    config = AgentConfig(
        openai_api_key="sk-openai-test",
        anthropic_api_key="sk-anthropic-test",
        openai_api_base="https://openai.test",
        anthropic_api_base="https://anthropic.test",
        output_directory=str(tmp_path),
        verbose=False,
    )

    conceptual = MagicMock()
    conceptual.model = "gpt-4o"
    practical = MagicMock()
    practical.model = "claude-sonnet-4-20250514"
    judge = MagicMock()
    validator = MagicMock()

    monkeypatch.setattr(
        workflow_module, "ConceptualGenerator", MagicMock(return_value=conceptual)
    )
    monkeypatch.setattr(
        workflow_module, "PracticalGenerator", MagicMock(return_value=practical)
    )
    monkeypatch.setattr(workflow_module, "Judge", MagicMock(return_value=judge))
    monkeypatch.setattr(workflow_module, "Validator", MagicMock(return_value=validator))

    return (
        workflow_module.QuizGenerationWorkflow(config=config),
        conceptual,
        practical,
        judge,
        validator,
    )


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
            {
                "question": "Q2",
                "focus": "practical",
                "generator": "practical",
                "model": practical.model,
            },
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
    assert (
        workflow._route_after_human_feedback({"human_action": "improve"}) == "improve"
    )
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
    assert '"questions"' in content
    assert "Q1" in content


def test_run_invokes_app_with_thread_id(tmp_path, monkeypatch, sample_chunk):
    workflow, _, _, _, _ = build_workflow(tmp_path, monkeypatch)

    workflow.app = MagicMock()
    workflow.app.invoke.return_value = {"final_questions": []}

    result = workflow.run(sample_chunk)

    assert result == {"final_questions": []}
    args, _kwargs = workflow.app.invoke.call_args
    assert args[1]["configurable"]["thread_id"] == sample_chunk["number"]


def test_run_batch_saves_only_when_questions_present(
    tmp_path, monkeypatch, sample_chunk
):
    workflow, _, _, _, _ = build_workflow(tmp_path, monkeypatch)

    chunks = [
        sample_chunk,
        {**sample_chunk, "number": "3", "title": "Aircraft Safety"},
    ]

    workflow.run = MagicMock(
        side_effect=[
            {"chunk": chunks[0], "final_questions": [{"question": "Q1"}]},
            {"chunk": chunks[1], "final_questions": []},
        ]
    )
    workflow._save_result = MagicMock()

    results = workflow.run_batch(chunks, save_output=True, output_dir=str(tmp_path))

    assert len(results) == 2
    workflow._save_result.assert_called_once_with(results[0], str(tmp_path))


# ─── Additional tests for uncovered lines ────────────────────────────────────


def build_workflow_with_refiner(tmp_path, monkeypatch):
    """Extended build_workflow that also mocks the Refiner."""
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_BASE", raising=False)
    monkeypatch.delenv("GEMINI_API_BASE", raising=False)
    config = AgentConfig(
        openai_api_key="sk-openai-test",
        anthropic_api_key="sk-anthropic-test",
        openai_api_base="https://openai.test",
        anthropic_api_base="https://anthropic.test",
        output_directory=str(tmp_path),
        verbose=False,
    )

    conceptual = MagicMock()
    conceptual.model = "gpt-4o"
    practical = MagicMock()
    practical.model = "claude-sonnet-4-20250514"
    judge = MagicMock()
    validator = MagicMock()
    refiner = MagicMock()

    monkeypatch.setattr(workflow_module, "ConceptualGenerator", MagicMock(return_value=conceptual))
    monkeypatch.setattr(workflow_module, "PracticalGenerator", MagicMock(return_value=practical))
    monkeypatch.setattr(workflow_module, "Judge", MagicMock(return_value=judge))
    monkeypatch.setattr(workflow_module, "Validator", MagicMock(return_value=validator))
    monkeypatch.setattr(workflow_module, "Refiner", MagicMock(return_value=refiner))

    wf = workflow_module.QuizGenerationWorkflow(config=config)
    return wf, conceptual, practical, judge, validator, refiner


def test_generate_conceptual_success(tmp_path, monkeypatch, sample_chunk):
    workflow, conceptual, _, _, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    conceptual.generate.return_value = {
        "question": "Q1",
        "focus": "conceptual",
        "generator": "conceptual",
        "model": "gpt-4o",
    }

    state = {"chunk": sample_chunk, "improvement_feedback": None}
    result = workflow._generate_conceptual(state)
    assert result["conceptual_qa"]["question"] == "Q1"
    conceptual.generate.assert_called_once_with(
        chunk=sample_chunk, improvement_feedback=None
    )


def test_generate_conceptual_with_feedback(tmp_path, monkeypatch, sample_chunk):
    workflow, conceptual, _, _, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    conceptual.generate.return_value = {"question": "Q1 refined"}

    state = {"chunk": sample_chunk, "improvement_feedback": "Make it harder"}
    result = workflow._generate_conceptual(state)
    assert result["conceptual_qa"]["question"] == "Q1 refined"
    conceptual.generate.assert_called_with(
        chunk=sample_chunk, improvement_feedback="Make it harder"
    )


def test_generate_conceptual_error(tmp_path, monkeypatch, sample_chunk):
    workflow, conceptual, _, _, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    conceptual.generate.side_effect = RuntimeError("API error")

    state = {"chunk": sample_chunk, "improvement_feedback": None}
    result = workflow._generate_conceptual(state)
    assert "errors" in result
    assert any("Conceptual generation error" in e for e in result["errors"])


def test_generate_practical_success(tmp_path, monkeypatch, sample_chunk):
    workflow, _, practical, _, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    practical.generate.return_value = {
        "question": "Q2",
        "focus": "practical",
        "generator": "practical",
        "model": "claude-sonnet-4-20250514",
    }

    state = {"chunk": sample_chunk, "improvement_feedback": None}
    result = workflow._generate_practical(state)
    assert result["practical_qa"]["question"] == "Q2"


def test_generate_practical_error(tmp_path, monkeypatch, sample_chunk):
    workflow, _, practical, _, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    practical.generate.side_effect = ValueError("Bad request")

    state = {"chunk": sample_chunk, "improvement_feedback": None}
    result = workflow._generate_practical(state)
    assert "errors" in result
    assert any("Practical generation error" in e for e in result["errors"])


def test_get_provider_config_all_branches(tmp_path, monkeypatch):
    workflow, _, _, _, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    # anthropic
    key, base = workflow._get_provider_config("anthropic")
    assert key == "sk-anthropic-test"
    assert base == "https://anthropic.test"

    # cohere (no base URL)
    workflow.config.cohere_api_key = "cohere-test"
    key, base = workflow._get_provider_config("cohere")
    assert key == "cohere-test"
    assert base is None

    # mistral
    workflow.config.mistral_api_key = "mistral-test"
    workflow.config.mistral_api_base = "https://mistral.test"
    key, base = workflow._get_provider_config("mistral")
    assert key == "mistral-test"
    assert base == "https://mistral.test"

    # gemini
    workflow.config.gemini_api_key = "gemini-test"
    workflow.config.gemini_api_base = "https://gemini.test"
    key, base = workflow._get_provider_config("gemini")
    assert key == "gemini-test"
    assert base == "https://gemini.test"

    # google (alias for gemini)
    key, base = workflow._get_provider_config("google")
    assert key == "gemini-test"

    # openai (fallthrough)
    key, base = workflow._get_provider_config("openai")
    assert key == "sk-openai-test"
    assert base == "https://openai.test"


def test_refine_questions_with_refinement(tmp_path, monkeypatch, sample_chunk):
    workflow, _, _, _, validator, refiner = build_workflow_with_refiner(tmp_path, monkeypatch)

    imperfect_validation = {
        "valid": True,
        "warnings": ["Could be clearer"],
        "issues": [],
        "score": 9,
        "checks_passed": {},
        "question_type": "conceptual",
    }
    refined_conceptual = {
        "question": "Q1 refined",
        "focus": "conceptual",
        "refiner_model": "gpt-4o",
    }
    refined_practical = {
        "question": "Q2 refined",
        "focus": "practical",
        "refiner_model": "gpt-4o",
    }

    refiner.refine_batch.return_value = [refined_conceptual, refined_practical]
    validator.validate_batch.return_value = [
        {"valid": True, "score": 10, "warnings": [], "issues": [], "question_type": "conceptual"},
        {"valid": True, "score": 10, "warnings": [], "issues": [], "question_type": "practical"},
    ]

    state = {
        "chunk": sample_chunk,
        "conceptual_qa": {"question": "Q1", "focus": "conceptual"},
        "practical_qa": {"question": "Q2", "focus": "practical"},
        "validation_results": [imperfect_validation, {**imperfect_validation, "question_type": "practical"}],
        "current_step": "validate_questions",
        "errors": [],
    }

    result = workflow._refine_questions(state)
    assert result["refined_conceptual_qa"]["question"] == "Q1 refined"
    assert result["refined_practical_qa"]["question"] == "Q2 refined"
    assert result["all_valid"] is True
    assert result["current_step"] == "refine_questions"


def test_refine_questions_no_refinement_needed(tmp_path, monkeypatch, sample_chunk):
    """Questions not refined (no refiner_model in output) so refined state not stored."""
    workflow, _, _, _, validator, refiner = build_workflow_with_refiner(tmp_path, monkeypatch)

    perfect_validation = {
        "valid": True,
        "warnings": [],
        "issues": [],
        "score": 10,
        "checks_passed": {},
        "question_type": "conceptual",
    }

    # Refiner returns original (no refiner_model key → no refinement occurred)
    refiner.refine_batch.return_value = [
        {"question": "Q1"},  # no refiner_model
    ]

    state = {
        "chunk": sample_chunk,
        "conceptual_qa": {"question": "Q1"},
        "practical_qa": None,
        "validation_results": [perfect_validation],
        "current_step": "validate_questions",
        "errors": [],
    }

    result = workflow._refine_questions(state)
    # No refined question stored since no refiner_model key
    assert result.get("refined_conceptual_qa") is None


def test_refine_questions_only_practical(tmp_path, monkeypatch, sample_chunk):
    """Edge case: only practical question exists (no conceptual)."""
    workflow, _, _, _, validator, refiner = build_workflow_with_refiner(tmp_path, monkeypatch)

    imperfect_validation = {
        "valid": False,
        "warnings": [],
        "issues": ["Bad question"],
        "score": 5,
        "checks_passed": {},
        "question_type": "practical",
    }
    refined_practical = {
        "question": "Q2 refined",
        "focus": "practical",
        "refiner_model": "gpt-4o",
    }

    refiner.refine_batch.return_value = [refined_practical]
    validator.validate_batch.return_value = [
        {"valid": True, "score": 10, "warnings": [], "issues": [], "question_type": "practical"},
    ]

    state = {
        "chunk": sample_chunk,
        "conceptual_qa": None,
        "practical_qa": {"question": "Q2", "focus": "practical"},
        "validation_results": [imperfect_validation],
        "current_step": "validate_questions",
        "errors": [],
    }

    result = workflow._refine_questions(state)
    assert result["refined_practical_qa"]["question"] == "Q2 refined"


def test_refine_questions_error_handling(tmp_path, monkeypatch, sample_chunk):
    workflow, _, _, _, _, refiner = build_workflow_with_refiner(tmp_path, monkeypatch)

    refiner.refine_batch.side_effect = RuntimeError("Boom")

    state = {
        "chunk": sample_chunk,
        "conceptual_qa": {"question": "Q1"},
        "practical_qa": None,
        "validation_results": [{"valid": False, "score": 5, "warnings": [], "issues": []}],
        "current_step": "validate_questions",
        "errors": [],
    }

    result = workflow._refine_questions(state)
    assert any("Refinement error" in e for e in result["errors"])


def test_judge_questions_accept_conceptual(tmp_path, monkeypatch, sample_chunk):
    workflow, conceptual, _, judge, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    judge.judge.return_value = {"decision": "accept_conceptual", "reasoning": "Only conceptual passes"}

    state = {
        "chunk": sample_chunk,
        "conceptual_qa": {"question": "Q1", "focus": "conceptual"},
        "practical_qa": {"question": "Q2", "focus": "practical"},
        "refined_conceptual_qa": None,
        "refined_practical_qa": None,
        "validation_results": [],
        "errors": [],
    }

    result = workflow._judge_questions(state)
    assert result["judge_decision"] == "accept_conceptual"
    assert len(result["final_questions"]) == 1
    assert result["final_questions"][0]["focus"] == "conceptual"


def test_judge_questions_accept_practical(tmp_path, monkeypatch, sample_chunk):
    workflow, _, practical, judge, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    judge.judge.return_value = {"decision": "accept_practical", "reasoning": "Only practical passes"}

    state = {
        "chunk": sample_chunk,
        "conceptual_qa": {"question": "Q1", "focus": "conceptual"},
        "practical_qa": {"question": "Q2", "focus": "practical"},
        "refined_conceptual_qa": None,
        "refined_practical_qa": None,
        "validation_results": [],
        "errors": [],
    }

    result = workflow._judge_questions(state)
    assert result["judge_decision"] == "accept_practical"
    assert len(result["final_questions"]) == 1
    assert result["final_questions"][0]["focus"] == "practical"


def test_judge_questions_reject_both(tmp_path, monkeypatch, sample_chunk):
    workflow, _, _, judge, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    judge.judge.return_value = {"decision": "reject_both", "reasoning": "Both fail"}

    state = {
        "chunk": sample_chunk,
        "conceptual_qa": {"question": "Q1", "focus": "conceptual"},
        "practical_qa": {"question": "Q2", "focus": "practical"},
        "refined_conceptual_qa": None,
        "refined_practical_qa": None,
        "validation_results": [],
        "errors": [],
    }

    result = workflow._judge_questions(state)
    assert result["judge_decision"] == "reject_both"
    assert result["final_questions"] == []


def test_judge_questions_error_handling(tmp_path, monkeypatch, sample_chunk):
    workflow, _, _, judge, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    judge.judge.side_effect = RuntimeError("Judge failed")

    state = {
        "chunk": sample_chunk,
        "conceptual_qa": {"question": "Q1"},
        "practical_qa": None,
        "refined_conceptual_qa": None,
        "refined_practical_qa": None,
        "validation_results": [],
        "errors": [],
    }

    result = workflow._judge_questions(state)
    assert any("Judge error" in e for e in result["errors"])


def test_judge_uses_refined_questions_when_available(tmp_path, monkeypatch, sample_chunk):
    workflow, conceptual, practical, judge, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    judge.judge.return_value = {"decision": "accept_both", "reasoning": "Both pass"}

    refined_c = {"question": "Q1 refined", "focus": "conceptual", "generator": "conceptual", "model": "gpt-4o"}
    refined_p = {"question": "Q2 refined", "focus": "practical", "generator": "practical", "model": "claude-test"}

    state = {
        "chunk": sample_chunk,
        "conceptual_qa": {"question": "Q1 original"},
        "practical_qa": {"question": "Q2 original"},
        "refined_conceptual_qa": refined_c,
        "refined_practical_qa": refined_p,
        "validation_results": [],
        "errors": [],
    }

    result = workflow._judge_questions(state)
    # Should use refined questions, not originals
    assert result["final_questions"][0]["question"] == "Q1 refined"
    assert result["final_questions"][1]["question"] == "Q2 refined"


def test_route_after_validation(tmp_path, monkeypatch):
    workflow, _, _, _, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    # No refined questions → go to refine
    assert workflow._route_after_validation({}) == "refine"
    assert workflow._route_after_validation({"refined_conceptual_qa": None}) == "refine"

    # Has refined questions → go to judge
    assert workflow._route_after_validation({"refined_conceptual_qa": {"question": "Q"}}) == "judge"
    assert workflow._route_after_validation({"refined_practical_qa": {"question": "Q"}}) == "judge"


def test_run_batch_no_save_when_disabled(tmp_path, monkeypatch, sample_chunk):
    workflow, _, _, _, _, _ = build_workflow_with_refiner(tmp_path, monkeypatch)

    chunks = [sample_chunk]
    workflow.run = MagicMock(
        return_value={"chunk": sample_chunk, "final_questions": [{"question": "Q1"}]}
    )
    workflow._save_result = MagicMock()

    results = workflow.run_batch(chunks, save_output=False, output_dir=str(tmp_path))

    assert len(results) == 1
    workflow._save_result.assert_not_called()
