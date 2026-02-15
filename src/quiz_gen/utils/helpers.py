"""
Utility helpers for quiz generation
"""

import json
from typing import Any, Dict


def parse_json_response(content: str) -> Dict[str, Any]:
    """
    Extract and parse JSON from LLM response content.
    
    Handles responses that may contain JSON wrapped in markdown code blocks.
    
    Args:
        content: Raw response text from LLM
        
    Returns:
        Parsed JSON as a dictionary
        
    Raises:
        json.JSONDecodeError: If content cannot be parsed as valid JSON
        ValueError: If content is empty or None
        
    Examples:
        >>> parse_json_response('{"key": "value"}')
        {'key': 'value'}
        
        >>> parse_json_response('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}
        
        >>> parse_json_response('```\\n{"key": "value"}\\n```')
        {'key': 'value'}
    """
    if not content:
        raise ValueError("Content cannot be empty or None")
    
    # Strip whitespace
    content = content.strip()
    
    # Extract JSON from markdown code blocks if present
    if "```json" in content:
        # Extract content between ```json and ```
        content = content.split("```json")[1].split("```", 1)[0].strip()
    elif "```" in content:
        # Extract content between ``` and ```
        content = content.split("```")[1].split("```")[0].strip()
    
    # Parse JSON
    return json.loads(content)


def validate_qa_structure(qa: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate basic structure of a quiz question.
    
    Args:
        qa: Quiz question dictionary
        
    Returns:
        Tuple of (is_valid, list_of_issues)
        
    Examples:
        >>> qa = {
        ...     "question": "What is AI?",
        ...     "options": {"A": "Intelligence", "B": "Code", "C": "Data", "D": "Network"},
        ...     "correct_answer": "A",
        ...     "explanations": {"A": "Correct", "B": "Wrong", "C": "Wrong", "D": "Wrong"}
        ... }
        >>> validate_qa_structure(qa)
        (True, [])
    """
    issues = []
    
    # Check required fields
    required_fields = ["question", "options", "correct_answer", "explanations"]
    for field in required_fields:
        if field not in qa:
            issues.append(f"Missing required field: {field}")
    
    if issues:
        return False, issues
    
    # Check options structure
    options = qa.get("options", {})
    if not isinstance(options, dict):
        issues.append("Options must be a dictionary")
    elif len(options) != 4:
        issues.append(f"Expected exactly 4 options, got {len(options)}")
    elif set(options.keys()) != {"A", "B", "C", "D"}:
        issues.append(f"Options must have keys A, B, C, D, got {set(options.keys())}")
    
    # Check correct answer
    correct_answer = qa.get("correct_answer")
    if correct_answer not in {"A", "B", "C", "D"}:
        issues.append(f"Correct answer must be A, B, C, or D, got {correct_answer}")
    
    # Check explanations structure
    explanations = qa.get("explanations", {})
    if not isinstance(explanations, dict):
        issues.append("Explanations must be a dictionary")
    elif len(explanations) != 4:
        issues.append(f"Expected exactly 4 explanations, got {len(explanations)}")
    elif set(explanations.keys()) != {"A", "B", "C", "D"}:
        issues.append(f"Explanations must have keys A, B, C, D, got {set(explanations.keys())}")
    
    return len(issues) == 0, issues


def build_chunk_context(chunk: Dict[str, Any]) -> str:
    """
    Build a formatted string representation of a regulation chunk.
    
    Args:
        chunk: Regulation chunk dictionary
        
    Returns:
        Formatted string for use in prompts
        
    Examples:
        >>> chunk = {
        ...     "title": "Safety Requirements",
        ...     "number": "42",
        ...     "section_type": "article",
        ...     "content": "All systems must be safe.",
        ...     "hierarchy_path": ["Regulation", "Chapter 4", "Article 42"]
        ... }
        >>> print(build_chunk_context(chunk))
        Section: Safety Requirements
        Number: 42
        Type: article
        Content: All systems must be safe.
        <BLANKLINE>
        Hierarchy: Regulation > Chapter 4 > Article 42
    """
    lines = []
    lines.append(f"Section: {chunk.get('title', 'Unknown')}")
    lines.append(f"Number: {chunk.get('number', 'N/A')}")
    lines.append(f"Type: {chunk.get('section_type', 'Unknown')}")
    lines.append(f"Content: {chunk.get('content', '')}")
    
    hierarchy = chunk.get('hierarchy_path', [])
    if hierarchy:
        lines.append(f"\nHierarchy: {' > '.join(hierarchy)}")
    
    return '\n'.join(lines)
