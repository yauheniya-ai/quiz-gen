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


ARTICLE = {
    "section_type": "article",
    "number": "50",
    "title": "Article 50 - Transparency obligations for providers and deployers of certain AI systems",
    "content": "1. Providers shall ensure that AI systems intended to interact directly with natural persons are designed and developed in such a way that the natural persons concerned are informed that they are interacting with an AI system, unless this is obvious from the point of view of a natural person who is reasonably well-informed, observant and circumspect, taking into account the circumstances and the context of use. This obligation shall not apply to AI systems authorised by law to detect, prevent, investigate or prosecute criminal offences, subject to appropriate safeguards for the rights and freedoms of third parties, unless those systems are available for the public to report a criminal offence.\n\n2. Providers of AI systems, including general-purpose AI systems, generating synthetic audio, image, video or text content, shall ensure that the outputs of the AI system are marked in a machine-readable format and detectable as artificially generated or manipulated. Providers shall ensure their technical solutions are effective, interoperable, robust and reliable as far as this is technically feasible, taking into account the specificities and limitations of various types of content, the costs of implementation and the generally acknowledged state of the art, as may be reflected in relevant technical standards. This obligation shall not apply to the extent the AI systems perform an assistive function for standard editing or do not substantially alter the input data provided by the deployer or the semantics thereof, or where authorised by law to detect, prevent, investigate or prosecute criminal offences.\n\n3. Deployers of an emotion recognition system or a biometric categorisation system shall inform the natural persons exposed thereto of the operation of the system, and shall process the personal data in accordance with Regulations (EU) 2016/679 and (EU) 2018/1725 and Directive (EU) 2016/680, as applicable. This obligation shall not apply to AI systems used for biometric categorisation and emotion recognition, which are permitted by law to detect, prevent or investigate criminal offences, subject to appropriate safeguards for the rights and freedoms of third parties, and in accordance with Union law.\n\n4. Deployers of an AI system that generates or manipulates image, audio or video content constituting a deep fake, shall disclose that the content has been artificially generated or manipulated. This obligation shall not apply where the use is authorised by law to detect, prevent, investigate or prosecute criminal offence. Where the content forms part of an evidently artistic, creative, satirical, fictional or analogous work or programme, the transparency obligations set out in this paragraph are limited to disclosure of the existence of such generated or manipulated content in an appropriate manner that does not hamper the display or enjoyment of the work.\n\nDeployers of an AI system that generates or manipulates text which is published with the purpose of informing the public on matters of public interest shall disclose that the text has been artificially generated or manipulated. This obligation shall not apply where the use is authorised by law to detect, prevent, investigate or prosecute criminal offences or where the AI-generated content has undergone a process of human review or editorial control and where a natural or legal person holds editorial responsibility for the publication of the content.\n\n5. The information referred to in paragraphs 1 to 4 shall be provided to the natural persons concerned in a clear and distinguishable manner at the latest at the time of the first interaction or exposure. The information shall conform to the applicable accessibility requirements.\n\n6. Paragraphs 1 to 4 shall not affect the requirements and obligations set out in Chapter III, and shall be without prejudice to other transparency obligations laid down in Union or national law for deployers of AI systems.\n\n7. The AI Office shall encourage and facilitate the drawing up of codes of practice at Union level to facilitate the effective implementation of the obligations regarding the detection and labelling of artificially generated or manipulated content. The Commission may adopt implementing acts to approve those codes of practice in accordance with the procedure laid down in Article 56 (6). If it deems the code is not adequate, the Commission may adopt an implementing act specifying common rules for the implementation of those obligations in accordance with the examination procedure laid down in Article 98(2).",
    "hierarchy_path": [
      "REGULATION (EU) 2024/1689 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL",
      "CHAPTER IV - TRANSPARENCY OBLIGATIONS FOR PROVIDERS AND DEPLOYERS OF CERTAIN AI SYSTEMS",
      "Article 50 - Transparency obligations for providers and deployers of certain AI systems"
    ],
    "metadata": {
      "id": "art_50",
      "subtitle": "Transparency obligations for providers and deployers of certain AI systems"
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
        conceptual_provider="openai",
        practical_provider="anthropic",
        validator_provider="mistral",
        refiner_provider="openai",
        judge_provider="mistral",
        conceptual_model="gpt-5-nano-2025-08-07",
        practical_model="claude-haiku-4-5-20251001",
        validator_model="mistral-small-latest",
        refiner_model="gpt-5-mini-2025-08-07",
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
        for i, val_result in enumerate(result["validation_results"], 1):
            question_type = "Conceptual" if i == 1 else "Practical"
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
