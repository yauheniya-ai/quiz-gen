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


_JUDGE_JSON = '{"decision": "accept_both", "reasoning": "Both good."}'


def test_judge_with_none_conceptual(practical_qa, validation_results, sample_chunk):
    """Test judging when conceptual_qa is None (practical generation only)."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=_JUDGE_JSON)]
    with patch("src.quiz_gen.agents.judge.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = Judge(api_key="test-key")
        result = agent.judge(None, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"


def test_judge_with_none_practical(conceptual_qa, validation_results, sample_chunk):
    """Test judging when practical_qa is None."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=_JUDGE_JSON)]
    with patch("src.quiz_gen.agents.judge.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = Judge(api_key="test-key")
        result = agent.judge(conceptual_qa, None, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"


def test_judge_cohere_provider(conceptual_qa, practical_qa, validation_results, sample_chunk):
    mock_response = MagicMock()
    mock_response.message.content = [MagicMock(text=_JUDGE_JSON)]
    with patch("src.quiz_gen.agents.judge.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        agent = Judge(provider="cohere", api_key="cohere-key", model="command-r-plus")
        result = agent.judge(conceptual_qa, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"
        assert result["judge_model"] == "command-r-plus"


def test_judge_cohere_markdown_fence(conceptual_qa, practical_qa, validation_results, sample_chunk):
    mock_response = MagicMock()
    mock_response.message.content = [MagicMock(text="```json\n" + _JUDGE_JSON + "\n```")]
    with patch("src.quiz_gen.agents.judge.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        agent = Judge(provider="cohere", api_key="cohere-key")
        result = agent.judge(conceptual_qa, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"


def test_judge_gemini_provider(conceptual_qa, practical_qa, validation_results, sample_chunk):
    mock_response = MagicMock()
    mock_response.text = _JUDGE_JSON
    with patch("src.quiz_gen.agents.judge.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        agent = Judge(provider="google", api_key="gemini-key", model="gemini-pro")
        result = agent.judge(conceptual_qa, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"
        assert result["judge_model"] == "gemini-pro"


def test_judge_gemini_markdown_fence(conceptual_qa, practical_qa, validation_results, sample_chunk):
    mock_response = MagicMock()
    mock_response.text = "```json\n" + _JUDGE_JSON + "\n```"
    with patch("src.quiz_gen.agents.judge.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        agent = Judge(provider="gemini", api_key="gemini-key")
        result = agent.judge(conceptual_qa, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"


def test_judge_mistral_provider(conceptual_qa, practical_qa, validation_results, sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=_JUDGE_JSON))]
    with patch("src.quiz_gen.agents.judge.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = Judge(provider="mistral", api_key="mistral-key", model="mistral-large")
        result = agent.judge(conceptual_qa, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"
        assert result["judge_model"] == "mistral-large"


def test_judge_mistral_markdown_fence(conceptual_qa, practical_qa, validation_results, sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="```json\n" + _JUDGE_JSON + "\n```"))]
    with patch("src.quiz_gen.agents.judge.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = Judge(provider="mistral", api_key="mistral-key")
        result = agent.judge(conceptual_qa, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"


def test_judge_openai_provider(conceptual_qa, practical_qa, validation_results, sample_chunk):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=_JUDGE_JSON))]
    with patch("src.quiz_gen.agents.judge.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = Judge(provider="openai", api_key="openai-key", model="gpt-4o")
        result = agent.judge(conceptual_qa, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"
        assert result["judge_model"] == "gpt-4o"


# ─── Additional tests for api_base and opposite fence types ───────────────


def test_judge_anthropic_with_api_base(conceptual_qa, practical_qa, validation_results, sample_chunk):
    """Cover api_base branch (line 74) in judge anthropic init."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=_JUDGE_JSON)]
    with patch("src.quiz_gen.agents.judge.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = Judge(
            provider="anthropic",
            api_key="sk-test",
            api_base="https://custom.anthropic.test",
        )
        result = agent.judge(conceptual_qa, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"


def test_judge_anthropic_plain_fence(conceptual_qa, practical_qa, validation_results, sample_chunk):
    """Cover the elif '```' body for anthropic provider."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="```\n" + _JUDGE_JSON + "\n```")]
    with patch("src.quiz_gen.agents.judge.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = Judge(provider="anthropic", api_key="sk-test")
        result = agent.judge(conceptual_qa, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"


def test_judge_cohere_plain_fence(conceptual_qa, practical_qa, validation_results, sample_chunk):
    """Cover the elif '```' body for cohere provider."""
    mock_response = MagicMock()
    mock_response.message.content = [MagicMock(text="```\n" + _JUDGE_JSON + "\n```")]
    with patch("src.quiz_gen.agents.judge.cohere") as mock_cohere_mod:
        mock_client = MagicMock()
        mock_client.chat.return_value = mock_response
        mock_cohere_mod.ClientV2.return_value = mock_client
        agent = Judge(provider="cohere", api_key="cohere-key")
        result = agent.judge(conceptual_qa, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"


def test_judge_gemini_plain_fence(conceptual_qa, practical_qa, validation_results, sample_chunk):
    """Cover the elif '```' body for gemini provider."""
    mock_response = MagicMock()
    mock_response.text = "```\n" + _JUDGE_JSON + "\n```"
    with patch("src.quiz_gen.agents.judge.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        agent = Judge(provider="gemini", api_key="gemini-key")
        result = agent.judge(conceptual_qa, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"


def test_judge_mistral_plain_fence(conceptual_qa, practical_qa, validation_results, sample_chunk):
    """Cover the elif '```' body for mistral provider."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="```\n" + _JUDGE_JSON + "\n```"))]
    with patch("src.quiz_gen.agents.judge.Mistral") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_cls.return_value = mock_client
        agent = Judge(provider="mistral", api_key="mistral-key")
        result = agent.judge(conceptual_qa, practical_qa, validation_results, sample_chunk)
        assert result["decision"] == "accept_both"

