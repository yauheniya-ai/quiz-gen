import pytest
from unittest.mock import MagicMock, patch
from src.quiz_gen.agents.refiner import Refiner


@pytest.fixture
def sample_chunk():
    return {
        "title": "Aircraft Maintenance",
        "number": "2",
        "section_type": "article",
        "content": "Aircraft must be maintained according to the approved schedule.",
        "hierarchy_path": ["Regulation", "Chapter 2", "Article 2"],
    }


@pytest.fixture
def sample_qa():
    return {
        "question": "What is required for aircraft maintenance?",
        "options": {
            "A": "Follow the approved schedule.",
            "B": "Ignore it.",
            "C": "Ask a passenger.",
            "D": "Wait.",
        },
        "correct_answer": "A",
        "explanations": {
            "A": "Correct.",
            "B": "Wrong.",
            "C": "Wrong.",
            "D": "Wrong.",
        },
        "difficulty": "easy",
        "focus": "conceptual",
        "generator": "conceptual",
        "model": "gpt-4o",
    }


@pytest.fixture
def perfect_validation():
    return {
        "valid": True,
        "warnings": [],
        "issues": [],
        "score": 10,
    }


@pytest.fixture
def imperfect_validation():
    return {
        "valid": True,
        "warnings": ["Question could be clearer"],
        "issues": [],
        "score": 9,
        "checks_passed": {
            "has_4_options": True,
            "has_correct_answer": True,
            "has_all_explanations": True,
            "explanations_concise": True,
            "question_clear": False,
            "correct_explanation": True,
            "wrong_explanations_are_hints": True,
            "options_plausible": True,
            "question_unambiguous": True,
            "regulation_based": True,
        },
    }


_REFINED_JSON = '{"question": "What must be done for aircraft maintenance?", "options": {"A": "Follow the approved schedule.", "B": "Ignore it.", "C": "Ask a passenger.", "D": "Wait."}, "correct_answer": "A", "explanations": {"A": "Correct.", "B": "Wrong.", "C": "Wrong.", "D": "Wrong."}, "difficulty": "easy", "focus": "conceptual", "refinement_notes": "Improved question clarity."}'


def test_refine_perfect_returns_early(sample_qa, perfect_validation, sample_chunk):
    """Perfect validation (valid, score=10, no warnings/issues) should skip LLM call."""
    refiner = Refiner(api_key="test-key")
    result = refiner.refine(sample_qa, perfect_validation, sample_chunk)
    assert (
        result["refinement_notes"]
        == "No refinement needed (perfect score, no warnings or issues)"
    )
    # Original fields preserved
    assert result["question"] == sample_qa["question"]
    assert result["correct_answer"] == "A"


def test_refine_with_none_warnings_and_issues(sample_qa, sample_chunk):
    """None warnings/issues should be treated as empty - but score < 10 triggers refinement."""
    # valid=True but score=8 means refinement IS needed
    validation = {
        "valid": True,
        "warnings": None,
        "issues": None,
        "score": 8,
        "checks_passed": {},
    }
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=_REFINED_JSON))]
    with patch("src.quiz_gen.agents.refiner.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_cls.return_value = mock_client
        refiner = Refiner(api_key="test-key")
        result = refiner.refine(sample_qa, validation, sample_chunk)
        assert result["refinement_notes"] == "Improved question clarity."
        assert result["refiner_model"] == "gpt-4o"


def test_refine_openai_provider(sample_qa, imperfect_validation, sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=_REFINED_JSON))]
    with patch("src.quiz_gen.agents.refiner.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_cls.return_value = mock_client
        refiner = Refiner(provider="openai", api_key="test-key", model="gpt-4o-mini")
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["refiner_model"] == "gpt-4o-mini"
        assert result["generator"] == "conceptual"
        assert result["model"] == "gpt-4o"
        assert result["question"] == "What must be done for aircraft maintenance?"


def test_refine_anthropic_provider(sample_qa, imperfect_validation, sample_chunk):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=_REFINED_JSON)]
    with patch("src.quiz_gen.agents.refiner.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        refiner = Refiner(
            provider="anthropic",
            api_key="sk-test",
            api_base="https://anthropic.test",
            model="claude-3-haiku",
        )
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["refiner_model"] == "claude-3-haiku"
        assert result["generator"] == "conceptual"
        assert result["refinement_notes"] == "Improved question clarity."


def test_refine_anthropic_markdown_fence(sample_qa, imperfect_validation, sample_chunk):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="```json\n" + _REFINED_JSON + "\n```")]
    with patch("src.quiz_gen.agents.refiner.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        refiner = Refiner(provider="anthropic", api_key="sk-test")
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["correct_answer"] == "A"


def test_refine_cohere_provider(sample_qa, imperfect_validation, sample_chunk):
    mock_response = MagicMock()
    mock_response.message.content = [MagicMock(text=_REFINED_JSON)]
    with patch("src.quiz_gen.agents.refiner.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        refiner = Refiner(
            provider="cohere", api_key="cohere-key", model="command-r-plus"
        )
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["refiner_model"] == "command-r-plus"
        assert result["generator"] == "conceptual"


def test_refine_cohere_markdown_fence(sample_qa, imperfect_validation, sample_chunk):
    mock_response = MagicMock()
    mock_response.message.content = [MagicMock(text="```\n" + _REFINED_JSON + "\n```")]
    with patch("src.quiz_gen.agents.refiner.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        refiner = Refiner(provider="cohere", api_key="cohere-key")
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["correct_answer"] == "A"


def test_refine_gemini_provider(sample_qa, imperfect_validation, sample_chunk):
    mock_response = MagicMock()
    mock_response.text = _REFINED_JSON
    with patch("src.quiz_gen.agents.refiner.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        refiner = Refiner(provider="google", api_key="gemini-key", model="gemini-pro")
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["refiner_model"] == "gemini-pro"
        assert result["generator"] == "conceptual"


def test_refine_gemini_markdown_fence(sample_qa, imperfect_validation, sample_chunk):
    mock_response = MagicMock()
    mock_response.text = "```json\n" + _REFINED_JSON + "\n```"
    with patch("src.quiz_gen.agents.refiner.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        refiner = Refiner(provider="gemini", api_key="gemini-key")
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["correct_answer"] == "A"


def test_refine_mistral_provider(sample_qa, imperfect_validation, sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=_REFINED_JSON))]
    with patch("src.quiz_gen.agents.refiner.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        refiner = Refiner(
            provider="mistral", api_key="mistral-key", model="mistral-large"
        )
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["refiner_model"] == "mistral-large"
        assert result["generator"] == "conceptual"


def test_refine_mistral_markdown_fence(sample_qa, imperfect_validation, sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="```json\n" + _REFINED_JSON + "\n```"))
    ]
    with patch("src.quiz_gen.agents.refiner.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        refiner = Refiner(provider="mistral", api_key="mistral-key")
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["correct_answer"] == "A"


def test_refine_preserves_metadata(sample_qa, imperfect_validation, sample_chunk):
    """Refiner must preserve generator and model from the original QA."""
    qa = {**sample_qa, "generator": "practical", "model": "claude-test"}
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=_REFINED_JSON))]
    with patch("src.quiz_gen.agents.refiner.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_cls.return_value = mock_client
        refiner = Refiner(api_key="test-key")
        result = refiner.refine(qa, imperfect_validation, sample_chunk)
        assert result["generator"] == "practical"
        assert result["model"] == "claude-test"


def test_refine_preserves_unknown_generator(
    sample_qa, imperfect_validation, sample_chunk
):
    """If generator not in original QA, defaults to 'unknown'."""
    qa = {k: v for k, v in sample_qa.items() if k not in ("generator", "model")}
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=_REFINED_JSON))]
    with patch("src.quiz_gen.agents.refiner.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_cls.return_value = mock_client
        refiner = Refiner(api_key="test-key")
        result = refiner.refine(qa, imperfect_validation, sample_chunk)
        assert result["generator"] == "unknown"


def test_refine_batch(
    sample_qa, imperfect_validation, perfect_validation, sample_chunk
):
    """refine_batch should refine each qa/validation pair in order."""
    qa2 = {**sample_qa, "question": "Another question?", "focus": "practical"}
    with patch.object(
        Refiner,
        "refine",
        side_effect=[
            {**sample_qa, "refinement_notes": "fixed 1"},
            {
                **qa2,
                "refinement_notes": "No refinement needed (perfect score, no warnings or issues)",
            },
        ],
    ):
        refiner = Refiner(api_key="test-key")
        results = refiner.refine_batch(
            [sample_qa, qa2],
            [imperfect_validation, perfect_validation],
            sample_chunk,
        )
        assert len(results) == 2
        assert results[0]["refinement_notes"] == "fixed 1"
        assert "No refinement needed" in results[1]["refinement_notes"]


def test_refine_invalid_validation_triggers_refinement(sample_qa, sample_chunk):
    """valid=False should always trigger refinement even if score is 10."""
    validation = {
        "valid": False,
        "warnings": [],
        "issues": ["Bad question"],
        "score": 7,
        "checks_passed": {},
    }
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=_REFINED_JSON))]
    with patch("src.quiz_gen.agents.refiner.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_cls.return_value = mock_client
        refiner = Refiner(api_key="test-key")
        result = refiner.refine(sample_qa, validation, sample_chunk)
        assert result["refiner_model"] == "gpt-4o"
        assert result["refinement_notes"] == "Improved question clarity."


# ─── Additional tests for opposite fence types ────────────────────────────────


def test_refine_anthropic_plain_fence(sample_qa, imperfect_validation, sample_chunk):
    """Cover the elif '```' body for anthropic provider (line 141)."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="```\n" + _REFINED_JSON + "\n```")]
    with patch("src.quiz_gen.agents.refiner.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        refiner = Refiner(provider="anthropic", api_key="sk-test")
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["correct_answer"] == "A"


def test_refine_cohere_json_fence(sample_qa, imperfect_validation, sample_chunk):
    """Cover the if '```json' body for cohere provider (line 153)."""
    mock_response = MagicMock()
    mock_response.message.content = [
        MagicMock(text="```json\n" + _REFINED_JSON + "\n```")
    ]
    with patch("src.quiz_gen.agents.refiner.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        refiner = Refiner(provider="cohere", api_key="cohere-key")
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["correct_answer"] == "A"


def test_refine_gemini_plain_fence(sample_qa, imperfect_validation, sample_chunk):
    """Cover the elif '```' body for gemini provider (line 169)."""
    mock_response = MagicMock()
    mock_response.text = "```\n" + _REFINED_JSON + "\n```"
    with patch("src.quiz_gen.agents.refiner.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        refiner = Refiner(provider="gemini", api_key="gemini-key")
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["correct_answer"] == "A"


def test_refine_mistral_plain_fence(sample_qa, imperfect_validation, sample_chunk):
    """Cover the elif '```' body for mistral provider (line 183)."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="```\n" + _REFINED_JSON + "\n```"))
    ]
    with patch("src.quiz_gen.agents.refiner.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        refiner = Refiner(provider="mistral", api_key="mistral-key")
        result = refiner.refine(sample_qa, imperfect_validation, sample_chunk)
        assert result["correct_answer"] == "A"
