import pytest
from unittest.mock import MagicMock, patch
from src.quiz_gen.agents.practical_generator import PracticalGenerator

@pytest.fixture
def sample_chunk():
    return {
        "title": "Aircraft Maintenance",
        "number": "2",
        "section_type": "article",
        "content": "Aircraft must be maintained according to the approved schedule.",
        "hierarchy_path": ["Regulation", "Chapter 2", "Article 2"]
    }

def test_generate_calls_anthropic_and_parses_response(sample_chunk):
    mock_response = MagicMock()
    # Simulate Claude returning a JSON string in a markdown code block
    mock_response.content = [MagicMock(text="""```json\n{\"question\": \"What should a pilot do if the aircraft is due for maintenance?\", \"options\": {\"A\": \"Ignore the schedule.\", \"B\": \"Follow the approved maintenance schedule.\", \"C\": \"Ask a passenger.\", \"D\": \"Wait until a problem occurs.\"}, \"correct_answer\": \"B\", \"explanations\": {\"A\": \"Ignoring the schedule is unsafe.\", \"B\": \"This is the correct action.\", \"C\": \"Passengers are not responsible.\", \"D\": \"Waiting is not compliant.\"}, \"source_reference\": \"Article 2\", \"difficulty\": \"easy\", \"focus\": \"practical\"}\n```""")]
    with patch('src.quiz_gen.agents.practical_generator.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        agent = PracticalGenerator(api_key="test-key")
        result = agent.generate(sample_chunk)
        assert result["question"].startswith("What should")
        assert result["correct_answer"] == "B"
        assert result["generator"] == "practical"
        assert result["model"] == "claude-sonnet-4-20250514"
        assert "options" in result
        assert "explanations" in result

def test_generate_handles_plain_json_response(sample_chunk):
    mock_response = MagicMock()
    # Simulate Claude returning a plain JSON string (no markdown)
    mock_response.content = [MagicMock(text='{"question": "What should a pilot do if the aircraft is due for maintenance?", "options": {"A": "Ignore the schedule.", "B": "Follow the approved maintenance schedule.", "C": "Ask a passenger.", "D": "Wait until a problem occurs."}, "correct_answer": "B", "explanations": {"A": "Ignoring the schedule is unsafe.", "B": "This is the correct action.", "C": "Passengers are not responsible.", "D": "Waiting is not compliant."}, "source_reference": "Article 2", "difficulty": "easy", "focus": "practical"}')]
    with patch('src.quiz_gen.agents.practical_generator.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        agent = PracticalGenerator(api_key="test-key")
        result = agent.generate(sample_chunk)
        assert result["question"].startswith("What should")
        assert result["focus"] == "practical"
        assert result["generator"] == "practical"
        assert result["model"] == "claude-sonnet-4-20250514"

def test_generate_with_feedback(sample_chunk):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"question": "What should a pilot do if the aircraft is due for maintenance?", "options": {"A": "Ignore the schedule.", "B": "Follow the approved maintenance schedule.", "C": "Ask a passenger.", "D": "Wait until a problem occurs."}, "correct_answer": "B", "explanations": {"A": "Ignoring the schedule is unsafe.", "B": "This is the correct action.", "C": "Passengers are not responsible.", "D": "Waiting is not compliant."}, "source_reference": "Article 2", "difficulty": "easy", "focus": "practical"}')]
    with patch('src.quiz_gen.agents.practical_generator.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        agent = PracticalGenerator(api_key="test-key")
        feedback = "Make the scenario more realistic."
        result = agent.generate(sample_chunk, improvement_feedback=feedback)
        assert result["question"].startswith("What should")
        assert result["focus"] == "practical"
        assert result["generator"] == "practical"
        assert result["model"] == "claude-sonnet-4-20250514"
