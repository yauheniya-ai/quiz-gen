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


_CONCEPTUAL_JSON = '{"question": "What is an unmanned aircraft?", "options": {"A": "Aircraft without pilot.", "B": "Manned aircraft.", "C": "Paper plane.", "D": "Kite."}, "correct_answer": "A", "explanations": {"A": "Correct.", "B": "Wrong.", "C": "Wrong.", "D": "Wrong."}, "difficulty": "easy", "focus": "conceptual"}'


def test_generate_anthropic_provider(sample_chunk):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=_CONCEPTUAL_JSON)]
    with patch("src.quiz_gen.agents.conceptual_generator.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = ConceptualGenerator(
            api_key="test-key",
            api_base="https://anthropic.test",
            provider="anthropic",
            model="claude-3-opus-20240229",
        )
        result = agent.generate(sample_chunk)
        assert result["generator"] == "conceptual"
        assert result["model"] == "claude-3-opus-20240229"
        assert result["correct_answer"] == "A"


def test_generate_anthropic_provider_markdown_fence(sample_chunk):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="```json\n" + _CONCEPTUAL_JSON + "\n```")]
    with patch("src.quiz_gen.agents.conceptual_generator.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = ConceptualGenerator(provider="anthropic", api_key="sk-test")
        result = agent.generate(sample_chunk)
        assert result["correct_answer"] == "A"


def test_generate_cohere_provider(sample_chunk):
    mock_response = MagicMock()
    mock_response.message.content = [MagicMock(text=_CONCEPTUAL_JSON)]
    with patch("src.quiz_gen.agents.conceptual_generator.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        agent = ConceptualGenerator(provider="cohere", api_key="cohere-key", model="command-r-plus")
        result = agent.generate(sample_chunk)
        assert result["generator"] == "conceptual"
        assert result["model"] == "command-r-plus"


def test_generate_cohere_provider_markdown_fence(sample_chunk):
    mock_response = MagicMock()
    mock_response.message.content = [MagicMock(text="```\n" + _CONCEPTUAL_JSON + "\n```")]
    with patch("src.quiz_gen.agents.conceptual_generator.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        agent = ConceptualGenerator(provider="cohere", api_key="cohere-key")
        result = agent.generate(sample_chunk)
        assert result["correct_answer"] == "A"


def test_generate_gemini_provider(sample_chunk):
    mock_response = MagicMock()
    mock_response.text = _CONCEPTUAL_JSON
    with patch("src.quiz_gen.agents.conceptual_generator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        agent = ConceptualGenerator(provider="google", api_key="gemini-key", model="gemini-pro")
        result = agent.generate(sample_chunk)
        assert result["generator"] == "conceptual"
        assert result["model"] == "gemini-pro"


def test_generate_gemini_provider_markdown_fence(sample_chunk):
    mock_response = MagicMock()
    mock_response.text = "```json\n" + _CONCEPTUAL_JSON + "\n```"
    with patch("src.quiz_gen.agents.conceptual_generator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        agent = ConceptualGenerator(provider="gemini", api_key="gemini-key")
        result = agent.generate(sample_chunk)
        assert result["correct_answer"] == "A"


def test_generate_mistral_provider(sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=_CONCEPTUAL_JSON))]
    with patch("src.quiz_gen.agents.conceptual_generator.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = ConceptualGenerator(provider="mistral", api_key="mistral-key", model="mistral-large")
        result = agent.generate(sample_chunk)
        assert result["generator"] == "conceptual"
        assert result["model"] == "mistral-large"


def test_generate_mistral_provider_markdown_fence(sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="```json\n" + _CONCEPTUAL_JSON + "\n```"))]
    with patch("src.quiz_gen.agents.conceptual_generator.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = ConceptualGenerator(provider="mistral", api_key="mistral-key")
        result = agent.generate(sample_chunk)
        assert result["correct_answer"] == "A"
