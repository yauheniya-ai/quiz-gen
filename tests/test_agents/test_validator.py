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
