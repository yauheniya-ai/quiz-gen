"""
Unit tests for utility helpers
"""

import pytest
import json
from src.quiz_gen.utils.helpers import (
    parse_json_response,
    validate_qa_structure,
    build_chunk_context,
)


class TestParseJsonResponse:
    """Test JSON response parsing from various formats"""

    def test_parse_plain_json(self):
        """Plain JSON without markdown should parse correctly"""
        content = '{"key": "value", "number": 42}'
        result = parse_json_response(content)
        assert result == {"key": "value", "number": 42}

    def test_parse_json_with_json_markdown(self):
        """JSON wrapped in ```json blocks should extract correctly"""
        content = '```json\n{"key": "value"}\n```'
        result = parse_json_response(content)
        assert result == {"key": "value"}

    def test_parse_json_with_generic_markdown(self):
        """JSON wrapped in ``` blocks should extract correctly"""
        content = '```\n{"key": "value"}\n```'
        result = parse_json_response(content)
        assert result == {"key": "value"}

    def test_parse_json_with_surrounding_text(self):
        """JSON in markdown with surrounding text should extract correctly"""
        content = 'Here is the result:\n```json\n{"status": "success"}\n```\nDone!'
        result = parse_json_response(content)
        assert result == {"status": "success"}

    def test_parse_complex_json(self):
        """Complex nested JSON should parse correctly"""
        content = '''```json
{
    "question": "What is AI?",
    "options": {
        "A": "Artificial Intelligence",
        "B": "Automated Interface",
        "C": "Advanced Integration",
        "D": "Analytical Instrument"
    },
    "correct_answer": "A",
    "explanations": {
        "A": "This is correct.",
        "B": "This is wrong.",
        "C": "This is wrong.",
        "D": "This is wrong."
    }
}
```'''
        result = parse_json_response(content)
        assert result["question"] == "What is AI?"
        assert len(result["options"]) == 4
        assert result["correct_answer"] == "A"

    def test_parse_empty_string_raises_error(self):
        """Empty string should raise ValueError"""
        with pytest.raises(ValueError, match="Content cannot be empty or None"):
            parse_json_response("")

    def test_parse_none_raises_error(self):
        """None should raise ValueError"""
        with pytest.raises(ValueError, match="Content cannot be empty or None"):
            parse_json_response(None)

    def test_parse_invalid_json_raises_error(self):
        """Invalid JSON should raise JSONDecodeError"""
        with pytest.raises(json.JSONDecodeError):
            parse_json_response('{"invalid": json}')

    def test_parse_whitespace_handling(self):
        """Leading/trailing whitespace should be handled"""
        content = '  \n  {"key": "value"}  \n  '
        result = parse_json_response(content)
        assert result == {"key": "value"}


class TestValidateQaStructure:
    """Test quiz question structure validation"""

    def test_valid_qa_structure(self):
        """Valid Q&A should pass validation"""
        qa = {
            "question": "What is AI?",
            "options": {
                "A": "Artificial Intelligence",
                "B": "Automated Interface",
                "C": "Advanced Integration",
                "D": "Analytical Instrument"
            },
            "correct_answer": "A",
            "explanations": {
                "A": "This is correct.",
                "B": "This is wrong.",
                "C": "This is wrong.",
                "D": "This is wrong."
            }
        }
        is_valid, issues = validate_qa_structure(qa)
        assert is_valid is True
        assert issues == []

    def test_missing_question_field(self):
        """Missing question field should fail"""
        qa = {
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "correct_answer": "A",
            "explanations": {"A": "Correct", "B": "Wrong", "C": "Wrong", "D": "Wrong"}
        }
        is_valid, issues = validate_qa_structure(qa)
        assert is_valid is False
        assert "Missing required field: question" in issues

    def test_missing_options_field(self):
        """Missing options field should fail"""
        qa = {
            "question": "What is AI?",
            "correct_answer": "A",
            "explanations": {"A": "Correct", "B": "Wrong", "C": "Wrong", "D": "Wrong"}
        }
        is_valid, issues = validate_qa_structure(qa)
        assert is_valid is False
        assert "Missing required field: options" in issues

    def test_missing_correct_answer_field(self):
        """Missing correct_answer field should fail"""
        qa = {
            "question": "What is AI?",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "explanations": {"A": "Correct", "B": "Wrong", "C": "Wrong", "D": "Wrong"}
        }
        is_valid, issues = validate_qa_structure(qa)
        assert is_valid is False
        assert "Missing required field: correct_answer" in issues

    def test_missing_explanations_field(self):
        """Missing explanations field should fail"""
        qa = {
            "question": "What is AI?",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "correct_answer": "A"
        }
        is_valid, issues = validate_qa_structure(qa)
        assert is_valid is False
        assert "Missing required field: explanations" in issues

    def test_wrong_number_of_options(self):
        """Not having exactly 4 options should fail"""
        qa = {
            "question": "What is AI?",
            "options": {"A": "1", "B": "2", "C": "3"},
            "correct_answer": "A",
            "explanations": {"A": "Correct", "B": "Wrong", "C": "Wrong"}
        }
        is_valid, issues = validate_qa_structure(qa)
        assert is_valid is False
        assert any("Expected exactly 4 options" in issue for issue in issues)

    def test_wrong_option_keys(self):
        """Options with wrong keys should fail"""
        qa = {
            "question": "What is AI?",
            "options": {"1": "First", "2": "Second", "3": "Third", "4": "Fourth"},
            "correct_answer": "A",
            "explanations": {"A": "Correct", "B": "Wrong", "C": "Wrong", "D": "Wrong"}
        }
        is_valid, issues = validate_qa_structure(qa)
        assert is_valid is False
        assert any("Options must have keys A, B, C, D" in issue for issue in issues)

    def test_invalid_correct_answer(self):
        """Correct answer not in A/B/C/D should fail"""
        qa = {
            "question": "What is AI?",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "correct_answer": "E",
            "explanations": {"A": "Wrong", "B": "Wrong", "C": "Wrong", "D": "Wrong"}
        }
        is_valid, issues = validate_qa_structure(qa)
        assert is_valid is False
        assert any("Correct answer must be A, B, C, or D" in issue for issue in issues)

    def test_wrong_number_of_explanations(self):
        """Not having exactly 4 explanations should fail"""
        qa = {
            "question": "What is AI?",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "correct_answer": "A",
            "explanations": {"A": "Correct", "B": "Wrong"}
        }
        is_valid, issues = validate_qa_structure(qa)
        assert is_valid is False
        assert any("Expected exactly 4 explanations" in issue for issue in issues)

    def test_wrong_explanation_keys(self):
        """Explanations with wrong keys should fail"""
        qa = {
            "question": "What is AI?",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "correct_answer": "A",
            "explanations": {"1": "One", "2": "Two", "3": "Three", "4": "Four"}
        }
        is_valid, issues = validate_qa_structure(qa)
        assert is_valid is False
        assert any("Explanations must have keys A, B, C, D" in issue for issue in issues)

    def test_options_not_dict(self):
        """Options as non-dict should fail"""
        qa = {
            "question": "What is AI?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanations": {"A": "Correct", "B": "Wrong", "C": "Wrong", "D": "Wrong"}
        }
        is_valid, issues = validate_qa_structure(qa)
        assert is_valid is False
        assert "Options must be a dictionary" in issues

    def test_explanations_not_dict(self):
        """Explanations as non-dict should fail"""
        qa = {
            "question": "What is AI?",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "correct_answer": "A",
            "explanations": ["Correct", "Wrong", "Wrong", "Wrong"]
        }
        is_valid, issues = validate_qa_structure(qa)
        assert is_valid is False
        assert "Explanations must be a dictionary" in issues


class TestBuildChunkContext:
    """Test regulation chunk context building"""

    def test_full_chunk_context(self):
        """Full chunk with all fields should format correctly"""
        chunk = {
            "title": "Safety Requirements",
            "number": "42",
            "section_type": "article",
            "content": "All systems must be safe.",
            "hierarchy_path": ["Regulation", "Chapter 4", "Article 42"]
        }
        result = build_chunk_context(chunk)
        assert "Section: Safety Requirements" in result
        assert "Number: 42" in result
        assert "Type: article" in result
        assert "Content: All systems must be safe." in result
        assert "Hierarchy: Regulation > Chapter 4 > Article 42" in result

    def test_minimal_chunk_context(self):
        """Chunk with missing fields should use defaults"""
        chunk = {}
        result = build_chunk_context(chunk)
        assert "Section: Unknown" in result
        assert "Number: N/A" in result
        assert "Type: Unknown" in result
        assert "Content:" in result

    def test_chunk_without_hierarchy(self):
        """Chunk without hierarchy should not include hierarchy line"""
        chunk = {
            "title": "Test",
            "number": "1",
            "section_type": "section",
            "content": "Test content"
        }
        result = build_chunk_context(chunk)
        assert "Hierarchy:" not in result

    def test_chunk_with_empty_hierarchy(self):
        """Chunk with empty hierarchy list should not include hierarchy line"""
        chunk = {
            "title": "Test",
            "number": "1",
            "section_type": "section",
            "content": "Test content",
            "hierarchy_path": []
        }
        result = build_chunk_context(chunk)
        assert "Hierarchy:" not in result
