import pytest
from unittest.mock import MagicMock, patch
from src.quiz_gen.agents.conceptual_generator import ConceptualGenerator


@pytest.fixture
def sample_chunk():
    return {
        "title": "Definition of Unmanned Aircraft",
        "number": "1",
        "section_type": "article",
        "content": "An unmanned aircraft is an aircraft that is operated without a pilot on board.",
        "hierarchy_path": ["Regulation", "Chapter 1", "Article 1"],
    }


def test_generate_calls_openai_and_parses_response(sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""{"question": "What is an unmanned aircraft?", "options": {"A": "An aircraft operated without a pilot on board.", "B": "A manned aircraft.", "C": "A paper plane.", "D": "A kite."}, "correct_answer": "A", "explanations": {"A": "This matches the definition.", "B": "Manned aircraft have pilots.", "C": "Paper planes are toys, not aircraft.", "D": "Kites are not aircraft."}, "source_reference": "Article 1", "difficulty": "easy", "focus": "conceptual"}"""
            )
        )
    ]
    with patch("src.quiz_gen.agents.conceptual_generator.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        agent = ConceptualGenerator(api_key="test-key", api_base="http://test")
        result = agent.generate(sample_chunk)
        assert result["question"].startswith("What is")
        assert result["correct_answer"] == "A"
        assert result["generator"] == "conceptual"
        assert result["model"] == "gpt-4o"
        assert "options" in result
        assert "explanations" in result


def test_generate_with_feedback(sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""{"question": "What is an unmanned aircraft?", "options": {"A": "An aircraft operated without a pilot on board.", "B": "A manned aircraft.", "C": "A paper plane.", "D": "A kite."}, "correct_answer": "A", "explanations": {"A": "This matches the definition.", "B": "Manned aircraft have pilots.", "C": "Paper planes are toys, not aircraft.", "D": "Kites are not aircraft."}, "source_reference": "Article 1", "difficulty": "easy", "focus": "conceptual"}"""
            )
        )
    ]
    with patch("src.quiz_gen.agents.conceptual_generator.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        agent = ConceptualGenerator(api_key="test-key", api_base="http://test")
        feedback = "Make the question more challenging."
        result = agent.generate(sample_chunk, improvement_feedback=feedback)
        assert result["question"].startswith("What is")
        assert result["focus"] == "conceptual"
        assert result["generator"] == "conceptual"
        assert result["model"] == "gpt-4o"
