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
        "hierarchy_path": ["Regulation", "Chapter 2", "Article 2"],
    }


def test_generate_calls_anthropic_and_parses_response(sample_chunk):
    mock_response = MagicMock()
    # Simulate Claude returning a JSON string in a markdown code block
    mock_response.content = [
        MagicMock(
            text="""```json\n{\"question\": \"What should a pilot do if the aircraft is due for maintenance?\", \"options\": {\"A\": \"Ignore the schedule.\", \"B\": \"Follow the approved maintenance schedule.\", \"C\": \"Ask a passenger.\", \"D\": \"Wait until a problem occurs.\"}, \"correct_answer\": \"B\", \"explanations\": {\"A\": \"Ignoring the schedule is unsafe.\", \"B\": \"This is the correct action.\", \"C\": \"Passengers are not responsible.\", \"D\": \"Waiting is not compliant.\"}, \"source_reference\": \"Article 2\", \"difficulty\": \"easy\", \"focus\": \"practical\"}\n```"""
        )
    ]
    with patch("src.quiz_gen.agents.practical_generator.Anthropic") as mock_anthropic:
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
    mock_response.content = [
        MagicMock(
            text='{"question": "What should a pilot do if the aircraft is due for maintenance?", "options": {"A": "Ignore the schedule.", "B": "Follow the approved maintenance schedule.", "C": "Ask a passenger.", "D": "Wait until a problem occurs."}, "correct_answer": "B", "explanations": {"A": "Ignoring the schedule is unsafe.", "B": "This is the correct action.", "C": "Passengers are not responsible.", "D": "Waiting is not compliant."}, "source_reference": "Article 2", "difficulty": "easy", "focus": "practical"}'
        )
    ]
    with patch("src.quiz_gen.agents.practical_generator.Anthropic") as mock_anthropic:
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
    mock_response.content = [
        MagicMock(
            text='{"question": "What should a pilot do if the aircraft is due for maintenance?", "options": {"A": "Ignore the schedule.", "B": "Follow the approved maintenance schedule.", "C": "Ask a passenger.", "D": "Wait until a problem occurs."}, "correct_answer": "B", "explanations": {"A": "Ignoring the schedule is unsafe.", "B": "This is the correct action.", "C": "Passengers are not responsible.", "D": "Waiting is not compliant."}, "source_reference": "Article 2", "difficulty": "easy", "focus": "practical"}'
        )
    ]
    with patch("src.quiz_gen.agents.practical_generator.Anthropic") as mock_anthropic:
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


_PRACTICAL_JSON = '{"question": "What should a pilot do?", "options": {"A": "Ignore it.", "B": "Follow the schedule.", "C": "Ask passenger.", "D": "Wait."}, "correct_answer": "B", "explanations": {"A": "Wrong.", "B": "Correct.", "C": "Wrong.", "D": "Wrong."}, "difficulty": "easy", "focus": "practical"}'


def test_generate_anthropic_markdown_fence(sample_chunk):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="```json\n" + _PRACTICAL_JSON + "\n```")]
    with patch("src.quiz_gen.agents.practical_generator.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = PracticalGenerator(provider="anthropic", api_key="sk-test")
        result = agent.generate(sample_chunk)
        assert result["correct_answer"] == "B"


def test_generate_cohere_provider(sample_chunk):
    mock_response = MagicMock()
    mock_response.message.content = [MagicMock(text=_PRACTICAL_JSON)]
    with patch("src.quiz_gen.agents.practical_generator.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        agent = PracticalGenerator(
            provider="cohere", api_key="cohere-key", model="command-r-plus"
        )
        result = agent.generate(sample_chunk)
        assert result["generator"] == "practical"
        assert result["model"] == "command-r-plus"


def test_generate_cohere_provider_markdown_fence(sample_chunk):
    mock_response = MagicMock()
    mock_response.message.content = [
        MagicMock(text="```\n" + _PRACTICAL_JSON + "\n```")
    ]
    with patch("src.quiz_gen.agents.practical_generator.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        agent = PracticalGenerator(provider="cohere", api_key="cohere-key")
        result = agent.generate(sample_chunk)
        assert result["correct_answer"] == "B"


def test_generate_gemini_provider(sample_chunk):
    mock_response = MagicMock()
    mock_response.text = _PRACTICAL_JSON
    with patch("src.quiz_gen.agents.practical_generator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        agent = PracticalGenerator(
            provider="google", api_key="gemini-key", model="gemini-pro"
        )
        result = agent.generate(sample_chunk)
        assert result["generator"] == "practical"
        assert result["model"] == "gemini-pro"


def test_generate_gemini_provider_markdown_fence(sample_chunk):
    mock_response = MagicMock()
    mock_response.text = "```json\n" + _PRACTICAL_JSON + "\n```"
    with patch("src.quiz_gen.agents.practical_generator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        agent = PracticalGenerator(provider="gemini", api_key="gemini-key")
        result = agent.generate(sample_chunk)
        assert result["correct_answer"] == "B"


def test_generate_mistral_provider(sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=_PRACTICAL_JSON))]
    with patch("src.quiz_gen.agents.practical_generator.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = PracticalGenerator(
            provider="mistral", api_key="mistral-key", model="mistral-large"
        )
        result = agent.generate(sample_chunk)
        assert result["generator"] == "practical"
        assert result["model"] == "mistral-large"


def test_generate_mistral_provider_markdown_fence(sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="```json\n" + _PRACTICAL_JSON + "\n```"))
    ]
    with patch("src.quiz_gen.agents.practical_generator.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = PracticalGenerator(provider="mistral", api_key="mistral-key")
        result = agent.generate(sample_chunk)
        assert result["correct_answer"] == "B"


def test_generate_openai_provider(sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=_PRACTICAL_JSON))]
    with patch("src.quiz_gen.agents.practical_generator.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = PracticalGenerator(
            provider="openai", api_key="openai-key", model="gpt-4o"
        )
        result = agent.generate(sample_chunk)
        assert result["generator"] == "practical"
        assert result["model"] == "gpt-4o"


# ─── Additional tests for opposite fence types and api_base ──────────────────


def test_generate_anthropic_with_api_base(sample_chunk):
    """Cover api_base branch (line 79) in practical generator anthropic init."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=_PRACTICAL_JSON)]
    with patch("src.quiz_gen.agents.practical_generator.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = PracticalGenerator(
            provider="anthropic",
            api_key="sk-test",
            api_base="https://custom.anthropic.test",
        )
        result = agent.generate(sample_chunk)
        assert result["generator"] == "practical"


def test_generate_anthropic_plain_fence(sample_chunk):
    """Cover the elif '```' body for anthropic provider."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="```\n" + _PRACTICAL_JSON + "\n```")]
    with patch("src.quiz_gen.agents.practical_generator.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = PracticalGenerator(provider="anthropic", api_key="sk-test")
        result = agent.generate(sample_chunk)
        assert result["correct_answer"] == "B"


def test_generate_cohere_json_fence(sample_chunk):
    """Cover the if '```json' body for cohere provider."""
    mock_response = MagicMock()
    mock_response.message.content = [
        MagicMock(text="```json\n" + _PRACTICAL_JSON + "\n```")
    ]
    with patch("src.quiz_gen.agents.practical_generator.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        agent = PracticalGenerator(provider="cohere", api_key="cohere-key")
        result = agent.generate(sample_chunk)
        assert result["correct_answer"] == "B"


def test_generate_gemini_plain_fence(sample_chunk):
    """Cover the elif '```' body for gemini provider."""
    mock_response = MagicMock()
    mock_response.text = "```\n" + _PRACTICAL_JSON + "\n```"
    with patch("src.quiz_gen.agents.practical_generator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        agent = PracticalGenerator(provider="gemini", api_key="gemini-key")
        result = agent.generate(sample_chunk)
        assert result["correct_answer"] == "B"


def test_generate_mistral_plain_fence(sample_chunk):
    """Cover the elif '```' body for mistral provider."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="```\n" + _PRACTICAL_JSON + "\n```"))
    ]
    with patch("src.quiz_gen.agents.practical_generator.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = PracticalGenerator(provider="mistral", api_key="mistral-key")
        result = agent.generate(sample_chunk)
        assert result["correct_answer"] == "B"
