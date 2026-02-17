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


ARTICLE =     {
    "section_type": "annex",
    "number": "II",
    "title": "ANNEX II - List of criminal offences referred to in Article 5(1), first subparagraph, point (h)(iii)",
    "content": "Criminal offences referred to in Article 5(1), first subparagraph, point (h)(iii):\n— terrorism,\n— trafficking in human beings,\n— sexual exploitation of children, and child pornography,\n— illicit trafficking in narcotic drugs or psychotropic substances,\n— illicit trafficking in weapons, munitions or explosives,\n— murder, grievous bodily injury,\n— illicit trade in human organs or tissue,\n— illicit trafficking in nuclear or radioactive materials,\n— kidnapping, illegal restraint or hostage-taking,\n— crimes within the jurisdiction of the International Criminal Court,\n— unlawful seizure of aircraft or ships,\n— rape,\n— environmental crime,\n— organised or armed robbery,\n— sabotage,\n— participation in a criminal organisation involved in one or more of the offences listed above.",
    "hierarchy_path": [
      "REGULATION (EU) 2024/1689 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL",
      "ANNEX II - List of criminal offences referred to in Article 5(1), first subparagraph, point (h)(iii)"
    ],
    "metadata": {
      "id": "anx_II",
      "subtitle": "List of criminal offences referred to in Article 5(1), first subparagraph, point (h)(iii)"
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
        conceptual_model="command-r-plus-08-2024",
        practical_provider="cohere",
        practical_model="command-r-plus-08-2024",
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
    # STEP 2: INITIAL VALIDATION
    # ========================================================================
    print("=" * 70)
    print("STEP 2: INITIAL VALIDATION (of original questions)")
    print("=" * 70)
    print()
    
    if result.get("initial_validation_results"):
        for val_result in result["initial_validation_results"]:
            question_type = val_result.get("question_type", "unknown").capitalize()
            print(f"{question_type} Question Validation:")
            print(f"  Valid: {val_result.get('valid', False)}")
            print(f"  Score: {val_result.get('score', 0)}/10")
            print(f"  Validator Model: {val_result.get('validator_model', 'N/A')}")
            print()
            
            print(f"  Issues: {val_result.get('issues', []) or '[]'}")
            print(f"  Warnings: {val_result.get('warnings', []) or '[]'}")
            print()
            
            checks = val_result.get("checks_passed", {})
            print(f"  Checks Passed:")
            if checks:
                for check_name, passed in checks.items():
                    status = "✓" if passed else "✗"
                    print(f"    {status} {check_name}: {passed}")
            else:
                print(f"    {checks}")
            print()
    else:
        print("No initial validation results available")
        print()

    # ========================================================================
    # STEP 3: REFINEMENT
    # ========================================================================
    print("=" * 70)
    print("STEP 3: REFINEMENT")
    print("=" * 70)
    print()

    refined_conceptual = result.get("refined_conceptual_qa")
    refined_practical = result.get("refined_practical_qa")

    if refined_conceptual:
        print("CONCEPTUAL QUESTION (refined):")
        print(f"  Refiner Model: {refined_conceptual.get('refiner_model', 'N/A')}")
        print(f"  Original Generator: {refined_conceptual.get('generator', 'N/A')} / {refined_conceptual.get('model', 'N/A')}")
        print(f"  Refinement Notes: {refined_conceptual.get('refinement_notes', 'N/A')}")
        print(f"  Question: {refined_conceptual.get('question', 'N/A')[:100]}...")
        print()

    if refined_practical:
        print("PRACTICAL QUESTION (refined):")
        print(f"  Refiner Model: {refined_practical.get('refiner_model', 'N/A')}")
        print(f"  Original Generator: {refined_practical.get('generator', 'N/A')} / {refined_practical.get('model', 'N/A')}")
        print(f"  Refinement Notes: {refined_practical.get('refinement_notes', 'N/A')}")
        print(f"  Question: {refined_practical.get('question', 'N/A')[:100]}...")
        print()

    if not refined_conceptual and not refined_practical:
        print("None (both questions had perfect scores: 10/10, no warnings or issues)")
        print()
    
    # ========================================================================
    # STEP 4: RE-VALIDATION (after refinement)
    # ========================================================================
    print("=" * 70)
    print("STEP 4: RE-VALIDATION (after refinement)")
    print("=" * 70)
    print()
    
    # Only show re-validation if refinement actually happened
    if refined_conceptual or refined_practical:
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
                
                print(f"  Issues: {val_result.get('issues', []) or '[]'}")
                print(f"  Warnings: {val_result.get('warnings', []) or '[]'}")
                print()
                
                checks = val_result.get("checks_passed", {})
                print(f"  Checks Passed:")
                if checks:
                    for check_name, passed in checks.items():
                        status = "✓" if passed else "✗"
                        print(f"    {status} {check_name}: {passed}")
                else:
                    print(f"    {checks}")
                print()
    else:
        print("None (no refinement was needed)")
        print()

    # ========================================================================
    # STEP 5: JUDGE DECISION
    # ========================================================================
    print("=" * 70)
    print("STEP 5: JUDGE DECISION")
    print("=" * 70)
    print()

    print(f"Decision: {result.get('judge_decision', 'N/A')}")
    print(f"Reasoning: {result.get('judge_reasoning', 'N/A')}")
    print()

    # ========================================================================
    # FINAL QUESTIONS (not a workflow step, just the output)
    # ========================================================================
    print("=" * 70)
    print("FINAL QUESTIONS")
    print("=" * 70)
    print()

    if result.get("final_questions"):
        for i, question in enumerate(result["final_questions"], 1):
            print(f"{'-' * 70}")
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
            print()
    else:
        print("No valid questions generated")
        print()

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
                "step_2_initial_validation": {
                    "initial_validation_results": result.get("initial_validation_results", []),
                },
                "step_3_refinement": {
                    "refined_conceptual_qa": result.get("refined_conceptual_qa"),
                    "refined_practical_qa": result.get("refined_practical_qa"),
                },
                "step_4_revalidation": {
                    "validation_results": result.get("validation_results", []),
                    "all_valid": result.get("all_valid", False),
                },
                "step_5_judge": {
                    "decision": result.get("judge_decision"),
                    "reasoning": result.get("judge_reasoning"),
                    "final_questions": result.get("final_questions", []),
                },
                "errors": result.get("errors", []),
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
    print("  • Step 1: Generation (original questions from generators)")
    print("  • Step 2: Initial Validation (of original questions)")
    print("  • Step 3: Refinement (refined questions with notes)")
    print("  • Step 4: Re-validation (validation after refinement)")
    print("  • Step 5: Judge (decision, reasoning & final questions)")
    print()


if __name__ == "__main__":
    main()
