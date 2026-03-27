import pytest
from unittest.mock import MagicMock, patch
from src.quiz_gen.agents.validator import Validator


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
def valid_qa():
    return {
        "question": "What is required for aircraft maintenance?",
        "options": {
            "A": "Follow the approved schedule.",
            "B": "Ignore the schedule.",
            "C": "Ask a passenger.",
            "D": "Wait until a problem occurs.",
        },
        "correct_answer": "A",
        "explanations": {
            "A": "This is the correct action.",
            "B": "Ignoring the schedule is unsafe.",
            "C": "Passengers are not responsible.",
            "D": "Waiting is not compliant.",
        },
        "source_reference": "Article 2",
        "difficulty": "easy",
        "focus": "conceptual",
    }


@pytest.fixture
def invalid_qa_missing_option():
    return {
        "question": "What is required for aircraft maintenance?",
        "options": {
            "A": "Follow the approved schedule.",
            "B": "Ignore the schedule.",
            "C": "Ask a passenger.",
        },  # Only 3 options
        "correct_answer": "A",
        "explanations": {
            "A": "This is the correct action.",
            "B": "Ignoring the schedule is unsafe.",
            "C": "Passengers are not responsible.",
        },
        "source_reference": "Article 2",
        "difficulty": "easy",
        "focus": "conceptual",
    }


def test_validate_valid_qa(valid_qa, sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"valid": true, "issues": [], "warnings": [], "checks_passed": {"has_4_options": true, "has_correct_answer": true, "has_all_explanations": true, "explanations_concise": true, "question_clear": true, "correct_explanation": true, "wrong_explanations_are_hints": true, "options_plausible": true, "question_unambiguous": true, "regulation_based": true}, "score": 10}'
            )
        )
    ]
    with patch("src.quiz_gen.agents.validator.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        validator = Validator(api_key="test-key")
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True
        assert result["score"] == 10
        assert result["checks_passed"]["has_4_options"] is True
        assert result["validator_model"] == "gpt-4o"


def test_validate_invalid_qa_missing_option(invalid_qa_missing_option, sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"valid": false, "issues": ["Not exactly 4 options"], "warnings": [], "checks_passed": {"has_4_options": false, "has_correct_answer": true, "has_all_explanations": false, "explanations_concise": true, "question_clear": true, "correct_explanation": true, "wrong_explanations_are_hints": true, "options_plausible": false, "question_unambiguous": true, "regulation_based": true}, "score": 7}'
            )
        )
    ]
    with patch("src.quiz_gen.agents.validator.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        validator = Validator(api_key="test-key")
        result = validator.validate(invalid_qa_missing_option, sample_chunk)
        assert result["valid"] is False
        assert "Not exactly 4 options" in result["issues"]
        assert result["checks_passed"]["has_4_options"] is False
        assert result["score"] < 10
        assert result["validator_model"] == "gpt-4o"


_VALID_RESULT = '{"valid": true, "issues": [], "warnings": [], "checks_passed": {"has_4_options": true, "has_correct_answer": true, "has_all_explanations": true, "explanations_concise": true, "question_clear": true, "correct_explanation": true, "wrong_explanations_are_hints": true, "options_plausible": true, "question_unambiguous": true, "regulation_based": true}, "score": 10}'


def test_validate_anthropic_provider(valid_qa, sample_chunk):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=_VALID_RESULT)]
    with patch("src.quiz_gen.agents.validator.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        validator = Validator(
            provider="anthropic", api_key="sk-test", model="claude-3-haiku"
        )
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True
        assert result["score"] == 10
        assert result["validator_model"] == "claude-3-haiku"


def test_validate_anthropic_markdown_fence(valid_qa, sample_chunk):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="```json\n" + _VALID_RESULT + "\n```")]
    with patch("src.quiz_gen.agents.validator.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        validator = Validator(
            provider="anthropic",
            api_key="sk-test",
            api_base="https://anthropic.test",
        )
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True


def test_validate_cohere_provider(valid_qa, sample_chunk):
    mock_response = MagicMock()
    mock_response.message.content = [MagicMock(text=_VALID_RESULT)]
    with patch("src.quiz_gen.agents.validator.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        validator = Validator(
            provider="cohere", api_key="cohere-key", model="command-r"
        )
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True
        assert result["validator_model"] == "command-r"


def test_validate_cohere_markdown_fence(valid_qa, sample_chunk):
    mock_response = MagicMock()
    mock_response.message.content = [MagicMock(text="```\n" + _VALID_RESULT + "\n```")]
    with patch("src.quiz_gen.agents.validator.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        validator = Validator(provider="cohere", api_key="cohere-key")
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True


def test_validate_gemini_provider(valid_qa, sample_chunk):
    mock_response = MagicMock()
    mock_response.text = _VALID_RESULT
    with patch("src.quiz_gen.agents.validator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        validator = Validator(
            provider="google", api_key="gemini-key", model="gemini-pro"
        )
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True
        assert result["validator_model"] == "gemini-pro"


def test_validate_gemini_markdown_fence(valid_qa, sample_chunk):
    mock_response = MagicMock()
    mock_response.text = "```json\n" + _VALID_RESULT + "\n```"
    with patch("src.quiz_gen.agents.validator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        validator = Validator(provider="gemini", api_key="gemini-key")
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True


def test_validate_mistral_provider(valid_qa, sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=_VALID_RESULT))]
    with patch("src.quiz_gen.agents.validator.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        validator = Validator(
            provider="mistral", api_key="mistral-key", model="mistral-large"
        )
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True
        assert result["validator_model"] == "mistral-large"


def test_validate_mistral_markdown_fence(valid_qa, sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="```json\n" + _VALID_RESULT + "\n```"))
    ]
    with patch("src.quiz_gen.agents.validator.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        validator = Validator(provider="mistral", api_key="mistral-key")
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True


def test_validate_batch(valid_qa, invalid_qa_missing_option, sample_chunk):
    # Patch validate to return different results for each call
    with patch.object(
        Validator,
        "validate",
        side_effect=[{"valid": True, "score": 10}, {"valid": False, "score": 7}],
    ):
        validator = Validator(api_key="test-key")
        results = validator.validate_batch(
            [valid_qa, invalid_qa_missing_option], sample_chunk
        )
        assert results[0]["valid"] is True
        assert results[1]["valid"] is False
        assert results[0]["score"] == 10
        assert results[1]["score"] == 7


# ─── Additional tests for opposite fence types ─────────────────────────


def test_validate_anthropic_plain_fence(valid_qa, sample_chunk):
    """Cover the elif '```' body for anthropic provider."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="```\n" + _VALID_RESULT + "\n```")]
    with patch("src.quiz_gen.agents.validator.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        validator = Validator(provider="anthropic", api_key="sk-test")
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True


def test_validate_cohere_json_fence(valid_qa, sample_chunk):
    """Cover the if '```json' body for cohere provider."""
    mock_response = MagicMock()
    mock_response.message.content = [
        MagicMock(text="```json\n" + _VALID_RESULT + "\n```")
    ]
    with patch("src.quiz_gen.agents.validator.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        validator = Validator(provider="cohere", api_key="cohere-key")
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True


def test_validate_gemini_plain_fence(valid_qa, sample_chunk):
    """Cover the elif '```' body for gemini provider."""
    mock_response = MagicMock()
    mock_response.text = "```\n" + _VALID_RESULT + "\n```"
    with patch("src.quiz_gen.agents.validator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        validator = Validator(provider="gemini", api_key="gemini-key")
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True


def test_validate_mistral_plain_fence(valid_qa, sample_chunk):
    """Cover the elif '```' body for mistral provider."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="```\n" + _VALID_RESULT + "\n```"))
    ]
    with patch("src.quiz_gen.agents.validator.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        validator = Validator(provider="mistral", api_key="mistral-key")
        result = validator.validate(valid_qa, sample_chunk)
        assert result["valid"] is True
