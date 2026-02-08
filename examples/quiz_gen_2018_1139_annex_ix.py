#!/usr/bin/env python3
"""
Test multi-agent workflow with ANNEX IX of Regulation (EU) 2018/1139
Simple test using chunked content directly
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports in main.


ANNEX_IX = {
    "section_type": "annex",
    "number": "IX",
    "title": "ANNEX IX",
    "content": """
4.   ESSENTIAL REQUIREMENTS FOR REGISTRATION OF UNMANNED AIRCRAFT AND THEIR OPERATORS AND MARKING OF UNMANNED AIRCRAFT

4.1.   Without prejudice to obligations of Member States under the Chicago Convention unmanned aircraft the design of which is subject to certification pursuant to Article 56(1) shall be registered in accordance with the implementing acts referred to in Article 57.

4.2.   Operators of unmanned aircraft shall be registered in accordance with the implementing acts referred to in Article 57, where they operate any of the following:

(a) unmanned aircraft which, in the case of impact, can transfer, to a human, kinetic energy above 80 Joules;

(b) unmanned aircraft the operation of which presents risks to privacy, protection of personal data, security or the environment;

(c) unmanned aircraft the design of which is subject to certification pursuant to Article 56(1).

4.3.   Where a requirement of registration applies pursuant to point 4.1 or 4.2, the unmanned aircraft concerned shall be individually marked and identified, in accordance with the implementing acts referred to in Article 57.""",
    "hierarchy_path": [
        "REGULATION (EU) 2018/1139 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL",
        "ANNEX IX",
    ],
    "metadata": {"id": "anx_IX", "subtitle": ""},
}


def main():
    """Test workflow with ANNEX IX"""

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from quiz_gen.agents.workflow import QuizGenerationWorkflow
    from quiz_gen.agents.config import AgentConfig

    print("=" * 70)
    print("Testing Multi-Agent Workflow with ANNEX IX")
    print("=" * 70)
    print()

    # Display article info
    print(f"Annex: {ANNEX_IX['title']}")
    print(f"Content preview: {ANNEX_IX['content'][:200]}...")
    print()

    # Initialize configuration
    print("Initializing configuration...")
    config = AgentConfig(auto_accept_valid=False, verbose=True)

    try:
        config.validate()
        print("✓ Configuration valid")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease set environment variables:")
        print("  export OPENAI_API_KEY='your-key'")
        print("  export ANTHROPIC_API_KEY='your-key'")
        return

    print()

    # Initialize workflow
    print("Initializing workflow...")
    workflow = QuizGenerationWorkflow(config)
    print("✓ Workflow initialized")
    print()

    # Run workflow for ANNEX X
    print("Running multi-agent workflow...")
    print("-" * 70)
    result = workflow.run(ANNEX_IX)
    print("-" * 70)
    print()

    # Display results
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()

    # Validation
    print(f"All Valid: {result.get('all_valid', False)}")
    if result.get("validation_results"):
        for i, val_result in enumerate(result["validation_results"], 1):
            print(f"\nValidation {i}:")
            print(f"  Valid: {val_result.get('valid', False)}")
            print(f"  Score: {val_result.get('score', 0)}/10")
            if val_result.get("issues"):
                print(f"  Issues: {', '.join(val_result['issues'])}")
    print()

    # Judge decision
    print(f"Judge Decision: {result.get('judge_decision', 'N/A')}")
    print(f"Judge Reasoning: {result.get('judge_reasoning', 'N/A')}")
    print()

    # Generated questions
    if result.get("final_questions"):
        print("=" * 70)
        print("GENERATED QUESTIONS")
        print("=" * 70)

        for i, question in enumerate(result["final_questions"], 1):
            print(f"\n{'─'*70}")
            print(f"Question {i} ({question.get('focus', 'unknown').upper()})")
            print(f"{'─'*70}")

            print(f"\n{question.get('question', 'N/A')}")

            print("\nOptions:")
            correct = question.get("correct_answer", "")
            for option, text in question.get("options", {}).items():
                marker = "✓" if option == correct else " "
                print(f"  [{marker}] {option}. {text}")

            print("\nExplanations:")
            for option, explanation in question.get("explanations", {}).items():
                marker = "✓" if option == correct else "✗"
                print(f"  {marker} {option}. {explanation}")

            print("\nMetadata:")
            print(f"  Difficulty: {question.get('difficulty', 'N/A')}")
            print(f"  Generator: {question.get('generator', 'N/A')}")
            print(f"  Model: {question.get('model', 'N/A')}")
    else:
        print("No valid questions generated")

    print()

    # Errors
    if result.get("errors"):
        print("=" * 70)
        print("ERRORS")
        print("=" * 70)
        for error in result["errors"]:
            print(f"  • {error}")
        print()

    # Save result
    output_dir = Path("data/quizzes/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "annex_ix_quiz.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "chunk": result["chunk"],
                "questions": result.get("final_questions", []),
                "judge_decision": result.get("judge_decision"),
                "judge_reasoning": result.get("judge_reasoning"),
                "validation_results": result.get("validation_results"),
                "all_valid": result.get("all_valid"),
                "errors": result.get("errors", []),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Result saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()
