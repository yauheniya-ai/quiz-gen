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


ARTICLE =   {
    "section_type": "article",
    "number": "61",
    "title": "Article 61 - Informed consent to participate in testing in real world conditions outside AI regulatory sandboxes",
    "content": "1. For the purpose of testing in real world conditions under Article 60, freely-given informed consent shall be obtained from the subjects of testing prior to their participation in such testing and after their having been duly informed with concise, clear, relevant, and understandable information regarding:\n\n(a) the nature and objectives of the testing in real world conditions and the possible inconvenience that may be linked to their participation;\n\n(b) the conditions under which the testing in real world conditions is to be conducted, including the expected duration of the subject or subjects’ participation;\n\n(c) their rights, and the guarantees regarding their participation, in particular their right to refuse to participate in, and the right to withdraw from, testing in real world conditions at any time without any resulting detriment and without having to provide any justification;\n\n(d) the arrangements for requesting the reversal or the disregarding of the predictions, recommendations or decisions of the AI system;\n\n(e) the Union-wide unique single identification number of the testing in real world conditions in accordance with Article 60(4) point (c), and the contact details of the provider or its legal representative from whom further information can be obtained.\n\n2. The informed consent shall be dated and documented and a copy shall be given to the subjects of testing or their legal representative.\n\n(a) the nature and objectives of the testing in real world conditions and the possible inconvenience that may be linked to their participation;\n\n(b) the conditions under which the testing in real world conditions is to be conducted, including the expected duration of the subject or subjects’ participation;\n\n(c) their rights, and the guarantees regarding their participation, in particular their right to refuse to participate in, and the right to withdraw from, testing in real world conditions at any time without any resulting detriment and without having to provide any justification;\n\n(d) the arrangements for requesting the reversal or the disregarding of the predictions, recommendations or decisions of the AI system;\n\n(e) the Union-wide unique single identification number of the testing in real world conditions in accordance with Article 60(4) point (c), and the contact details of the provider or its legal representative from whom further information can be obtained.",
    "hierarchy_path": [
      "REGULATION (EU) 2024/1689 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL",
      "CHAPTER VI - MEASURES IN SUPPORT OF INNOVATION",
      "Article 61 - Informed consent to participate in testing in real world conditions outside AI regulatory sandboxes"
    ],
    "metadata": {
      "id": "art_61",
      "subtitle": "Informed consent to participate in testing in real world conditions outside AI regulatory sandboxes"
    }
  }


def main():
    """Test workflow with different articles"""

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from quiz_gen.agents.workflow import QuizGenerationWorkflow
    from quiz_gen.agents.config import AgentConfig

    print("=" * 70)
    print("Testing Multi-Provider Workflow")
    print("=" * 70)
    print()

    print(f"Article: {ARTICLE['title']}")
    print(f"Content preview: {ARTICLE['content'][:250]}...")
    print()

    print("Initializing configuration...")
    config = AgentConfig(
        conceptual_provider="cohere",
        conceptual_model="command-a-03-2025",
        practical_provider="cohere",
        practical_model="command-a-03-2025",
        validator_provider="openai",
        validator_model="gpt-5-nano-2025-08-07",
        refiner_provider="anthropic",
        refiner_model="claude-haiku-4-5-20251001",
        judge_provider="mistral",
        judge_model="mistral-small-latest",
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
        print("  export COHERE_API_KEY='your-key'")
        return

    print()

    print("Initializing workflow...")
    workflow = QuizGenerationWorkflow(config)
    print("✓ Workflow initialized")
    print()

    print("=" * 70)
    print(f"Processing chunk: {ARTICLE['title']}")
    print("=" * 70)
    print()
    print("Running multi-agent workflow...")
    result = workflow.run(ARTICLE)
    print()

    print("=" * 70)
    print("WORKFLOW RESULTS - FULL TRANSPARENCY")
    print("=" * 70)
    print()

    # ========================================================================
    # STEP 1: ORIGINAL GENERATED QUESTIONS
    # ========================================================================
    print("=" * 70)
    print("STEP 1: ORIGINAL QUESTIONS FROM GENERATORS")
    print("=" * 70)
    print()

    if result.get("conceptual_qa"):
        print("CONCEPTUAL QUESTION (from generator):")
        print(f"  Model: {result['conceptual_qa'].get('model', 'N/A')}")
        print(f"  Question: {result['conceptual_qa'].get('question', 'N/A')[:100]}...")
        print(f"  Difficulty: {result['conceptual_qa'].get('difficulty', 'N/A')}")
        print()

    if result.get("practical_qa"):
        print("PRACTICAL QUESTION (from generator):")
        print(f"  Model: {result['practical_qa'].get('model', 'N/A')}")
        print(f"  Question: {result['practical_qa'].get('question', 'N/A')[:100]}...")
        print(f"  Difficulty: {result['practical_qa'].get('difficulty', 'N/A')}")
        print()

    # ========================================================================
    # STEP 2: VALIDATION RESULTS
    # ========================================================================
    print("=" * 70)
    print("STEP 2: VALIDATION RESULTS")
    print("=" * 70)
    print()

    print(f"All Valid: {result.get('all_valid', False)}")
    print()
    
    if result.get("validation_results"):
        for val_result in result["validation_results"]:
            question_type = val_result.get("question_type", "unknown").capitalize()
            print(f"{question_type} Question Validation:")
            print(f"  Valid: {val_result.get('valid', False)}")
            print(f"  Score: {val_result.get('score', 0)}/10")
            print(f"  Validator Model: {val_result.get('validator_model', 'N/A')}")
            print()
            
            # Show ALL parameters - even if empty/None
            print(f"  Issues: {val_result.get('issues', []) or '[]'}")
            print(f"  Warnings: {val_result.get('warnings', []) or '[]'}")
            print()
            
            # Show all checks passed - display complete dict
            checks = val_result.get("checks_passed", {})
            print(f"  Checks Passed:")
            if checks:
                for check_name, passed in checks.items():
                    status = "✓" if passed else "✗"
                    print(f"    {status} {check_name}: {passed}")
            else:
                print(f"    {checks}")
            print()

    # ========================================================================
    # STEP 3: REFINED QUESTIONS
    # ========================================================================
    print("=" * 70)
    print("STEP 3: REFINED QUESTIONS (if needed)")
    print("=" * 70)
    print()

    if result.get("refined_conceptual_qa"):
        print("CONCEPTUAL QUESTION (refined):")
        refined = result['refined_conceptual_qa']
        print(f"  Refiner Model: {refined.get('refiner_model', 'N/A')}")
        print(f"  Original Generator: {refined.get('generator', 'N/A')} / {refined.get('model', 'N/A')}")
        print(f"  Refinement Notes: {refined.get('refinement_notes', 'N/A')}")
        print(f"  Question: {refined.get('question', 'N/A')[:100]}...")
        print()

    if result.get("refined_practical_qa"):
        print("PRACTICAL QUESTION (refined):")
        refined = result['refined_practical_qa']
        print(f"  Refiner Model: {refined.get('refiner_model', 'N/A')}")
        print(f"  Original Generator: {refined.get('generator', 'N/A')} / {refined.get('model', 'N/A')}")
        print(f"  Refinement Notes: {refined.get('refinement_notes', 'N/A')}")
        print(f"  Question: {refined.get('question', 'N/A')[:100]}...")
        print()

    if not result.get("refined_conceptual_qa") and not result.get("refined_practical_qa"):
        print("No refinements needed - perfect scores (10/10) with no warnings or issues")
        print()

    # ========================================================================
    # STEP 4: JUDGE DECISION
    # ========================================================================
    print("=" * 70)
    print("STEP 4: JUDGE DECISION")
    print("=" * 70)
    print()

    print(f"Decision: {result.get('judge_decision', 'N/A')}")
    print(f"Reasoning: {result.get('judge_reasoning', 'N/A')}")
    print()

    # ========================================================================
    # STEP 5: FINAL ACCEPTED QUESTIONS
    # ========================================================================
    print("=" * 70)
    print("STEP 5: FINAL ACCEPTED QUESTIONS")
    print("=" * 70)
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
    output_file = output_dir / "multi_model_quiz.json"

    # Save comprehensive results with ALL intermediate steps for transparency
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "workflow_metadata": {
                    "conceptual_generator": {
                        "provider": config.conceptual_provider,
                        "model": config.conceptual_model,
                    },
                    "practical_generator": {
                        "provider": config.practical_provider,
                        "model": config.practical_model,
                    },
                    "validator": {
                        "provider": config.validator_provider,
                        "model": config.validator_model,
                    },
                    "refiner": {
                        "provider": config.refiner_provider,
                        "model": config.refiner_model,
                    },
                    "judge": {
                        "provider": config.judge_provider,
                        "model": config.judge_model,
                    },
                },
                "step_1_generation": {
                    "conceptual_qa": result.get("conceptual_qa"),
                    "practical_qa": result.get("practical_qa"),
                },
                "step_2_validation": {
                    "all_valid": result.get("all_valid", False),
                    "validation_results": result.get("validation_results", []),
                },
                "step_3_refinement": {
                    "refined_conceptual_qa": result.get("refined_conceptual_qa"),
                    "refined_practical_qa": result.get("refined_practical_qa"),
                },
                "step_4_judge": {
                    "decision": result.get("judge_decision"),
                    "reasoning": result.get("judge_reasoning"),
                },
                "step_5_final": {
                    "questions": result.get("final_questions", []),
                    "errors": result.get("errors", []),
                },
                "chunk": result["chunk"],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("=" * 70)
    print("RESULTS SAVED")
    print("=" * 70)
    print(f"Output file: {output_file}")
    print("All intermediate results from 5 workflow steps included:")
    print("  • Step 1: Generation (original questions)")
    print("  • Step 2: Validation (full validator output)")
    print("  • Step 3: Refinement (if needed)")
    print("  • Step 4: Judge (decision & reasoning)")
    print("  • Step 5: Final (accepted questions)")
    print()


if __name__ == "__main__":
    main()
