import pytest
from unittest.mock import MagicMock, patch
from src.quiz_gen.agents.judge import Judge


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
def conceptual_qa():
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
def practical_qa():
    return {
        "question": "What should a pilot do if the aircraft is due for maintenance?",
        "options": {
            "A": "Ignore the schedule.",
            "B": "Follow the approved maintenance schedule.",
            "C": "Ask a passenger.",
            "D": "Wait until a problem occurs.",
        },
        "correct_answer": "B",
        "explanations": {
            "A": "Ignoring the schedule is unsafe.",
            "B": "This is the correct action.",
            "C": "Passengers are not responsible.",
            "D": "Waiting is not compliant.",
        },
        "source_reference": "Article 2",
        "difficulty": "easy",
        "focus": "practical",
    }


@pytest.fixture
def validation_results():
    return [
        {"type": "conceptual", "score": 9, "pass": True, "issues": []},
        {"type": "practical", "score": 10, "pass": True, "issues": []},
    ]


def test_judge_accepts_both(
    conceptual_qa, practical_qa, validation_results, sample_chunk
):
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text="""```json\n{\"decision\": \"accept_both\", \"reasoning\": \"Both questions meet all requirements.\", \"improvements_made\": [], \"questions\": [ {\"question\": \"What is required for aircraft maintenance?\", \"options\": {\"A\": \"Follow the approved schedule.\", \"B\": \"Ignore the schedule.\", \"C\": \"Ask a passenger.\", \"D\": \"Wait until a problem occurs.\"}, \"correct_answer\": \"A\", \"explanations\": {\"A\": \"This is the correct action.\", \"B\": \"Ignoring the schedule is unsafe.\", \"C\": \"Passengers are not responsible.\", \"D\": \"Waiting is not compliant.\"}, \"source_reference\": \"Article 2\", \"difficulty\": \"easy\", \"focus\": \"conceptual\"}, {\"question\": \"What should a pilot do if the aircraft is due for maintenance?\", \"options\": {\"A\": \"Ignore the schedule.\", \"B\": \"Follow the approved maintenance schedule.\", \"C\": \"Ask a passenger.\", \"D\": \"Wait until a problem occurs.\"}, \"correct_answer\": \"B\", \"explanations\": {\"A\": \"Ignoring the schedule is unsafe.\", \"B\": \"This is the correct action.\", \"C\": \"Passengers are not responsible.\", \"D\": \"Waiting is not compliant.\"}, \"source_reference\": \"Article 2\", \"difficulty\": \"easy\", \"focus\": \"practical\"} ]}\n```"""
        )
    ]
    with patch("src.quiz_gen.agents.judge.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        agent = Judge(api_key="test-key")
        result = agent.judge(
            conceptual_qa, practical_qa, validation_results, sample_chunk
        )
        assert result["decision"] == "accept_both"
        assert result["judge_model"] == "claude-sonnet-4-20250514"
        assert len(result["questions"]) == 2
        assert result["questions"][0]["focus"] == "conceptual"
        assert result["questions"][1]["focus"] == "practical"


def test_judge_refines_one(
    conceptual_qa, practical_qa, validation_results, sample_chunk
):
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text='{"decision": "refine_conceptual", "reasoning": "Conceptual question needed clarity.", "improvements_made": ["Improved clarity"], "questions": [{"question": "What is required for aircraft maintenance? (refined)", "options": {"A": "Follow the approved schedule.", "B": "Ignore the schedule.", "C": "Ask a passenger.", "D": "Wait until a problem occurs."}, "correct_answer": "A", "explanations": {"A": "This is the correct action.", "B": "Ignoring the schedule is unsafe.", "C": "Passengers are not responsible.", "D": "Waiting is not compliant."}, "source_reference": "Article 2", "difficulty": "easy", "focus": "conceptual"}, {"question": "What should a pilot do if the aircraft is due for maintenance?", "options": {"A": "Ignore the schedule.", "B": "Follow the approved maintenance schedule.", "C": "Ask a passenger.", "D": "Wait until a problem occurs."}, "correct_answer": "B", "explanations": {"A": "Ignoring the schedule is unsafe.", "B": "This is the correct action.", "C": "Passengers are not responsible.", "D": "Waiting is not compliant."}, "source_reference": "Article 2", "difficulty": "easy", "focus": "practical"}]}'
        )
    ]
    with patch("src.quiz_gen.agents.judge.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        agent = Judge(api_key="test-key")
        result = agent.judge(
            conceptual_qa, practical_qa, validation_results, sample_chunk
        )
        assert result["decision"] == "refine_conceptual"
        assert "Improved clarity" in result["improvements_made"]
        assert result["questions"][0]["focus"] == "conceptual"
        assert result["questions"][1]["focus"] == "practical"


def test_judge_rejects_both(
    conceptual_qa, practical_qa, validation_results, sample_chunk
):
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text='{"decision": "reject_both", "reasoning": "Both questions failed validation.", "improvements_made": [], "questions": []}'
        )
    ]
    with patch("src.quiz_gen.agents.judge.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        agent = Judge(api_key="test-key")
        result = agent.judge(
            conceptual_qa, practical_qa, validation_results, sample_chunk
        )
        assert result["decision"] == "reject_both"
        assert result["questions"] == []
        assert result["judge_model"] == "claude-sonnet-4-20250514"
