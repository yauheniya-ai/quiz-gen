#!/usr/bin/env python3
"""
Test multi-agent workflow with provider-specific models per agent.
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports in main.


ARTICLE_4 = {
    "section_type": "article",
    "number": "4",
    "title": "Article 4 - AI literacy",
    "content": "Providers and deployers of AI systems shall take measures to ensure, to their best extent, a sufficient level of AI literacy of their staff and other persons dealing with the operation and use of AI systems on their behalf, taking into account their technical knowledge, experience, education and training and the context the AI systems are to be used in, and considering the persons or groups of persons on whom the AI systems are to be used.",
    "hierarchy_path": [
        "REGULATION (EU) 2024/1689 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL",
        "CHAPTER I - GENERAL PROVISIONS",
        "Article 4 - AI literacy",
    ],
    "metadata": {"id": "art_4", "subtitle": "AI literacy"},
}


def main():
    """Test workflow with ANNEX IX"""

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from quiz_gen.agents.workflow import QuizGenerationWorkflow
    from quiz_gen.agents.config import AgentConfig

    print("=" * 70)
    print("Testing Multi-Provider Workflow with Article 4")
    print("=" * 70)
    print()

    print(f"Article: {ARTICLE_4['title']}")
    print(f"Content preview: {ARTICLE_4['content'][:200]}...")
    print()

    print("Initializing configuration...")
    config = AgentConfig(
        conceptual_provider="openai",
        practical_provider="anthropic",
        validator_provider="google",
        judge_provider="mistral",
        conceptual_model="gpt-4o",
        practical_model="claude-sonnet-4-20250514",
        validator_model="gemini-2.5-flash",
        judge_model="mistral-large-latest",
        conceptual_temperature=1,
        practical_temperature=1,
        validator_temperature=1,
        judge_temperature=1,
        conceptual_max_tokens=2000,
        practical_max_tokens=2000,
        validator_max_tokens=2000,
        judge_max_tokens=3000,
        auto_accept_valid=False,
        verbose=True,
    )

    try:
        config.validate()
        print("✓ Configuration valid")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease set environment variables:")
        print("  export OPENAI_API_KEY='your-key'")
        print("  export ANTHROPIC_API_KEY='your-key'")
        print("  export GEMINI_API_KEY='your-key'")
        print("  export MISTRAL_API_KEY='your-key'")
        return

    print()

    print("Initializing workflow...")
    workflow = QuizGenerationWorkflow(config)
    print("✓ Workflow initialized")
    print()

    print("Running multi-agent workflow...")
    print("-" * 70)
    result = workflow.run(ARTICLE_4)
    print("-" * 70)
    print()

    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()

    print(f"All Valid: {result.get('all_valid', False)}")
    if result.get("validation_results"):
        for i, val_result in enumerate(result["validation_results"], 1):
            print(f"\nValidation {i}:")
            print(f"  Valid: {val_result.get('valid', False)}")
            print(f"  Score: {val_result.get('score', 0)}/10")
            if val_result.get("issues"):
                print(f"  Issues: {', '.join(val_result['issues'])}")
    print()

    print(f"Judge Decision: {result.get('judge_decision', 'N/A')}")
    print(f"Judge Reasoning: {result.get('judge_reasoning', 'N/A')}")
    print()

    if result.get("final_questions"):
        print("=" * 70)
        print("GENERATED QUESTIONS")
        print("=" * 70)

        for i, question in enumerate(result["final_questions"], 1):
            print(f"\n{'-' * 70}")
            print(f"Question {i} ({question.get('focus', 'unknown').upper()})")
            print(f"{'-' * 70}")

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

    if result.get("errors"):
        print("=" * 70)
        print("ERRORS")
        print("=" * 70)
        for error in result["errors"]:
            print(f"  • {error}")
        print()

    output_dir = Path("data/quizzes/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "article_4_multi_model_quiz.json"

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
