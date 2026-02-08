#!/usr/bin/env python3
"""
Test multi-agent workflow with Article 77 of Regulation (EU) 2018/1139
Simple test using chunked content directly
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for imports in main.


ARTICLE_77_CHUNK = {
    "section_type": "article",
    "number": "77",
    "title": "Article 77 - Airworthiness and environmental certification",
    "content": """1. With regard to the products, parts, non-installed equipment and equipment to control unmanned aircraft remotely, referred to in points (a) and (b)(i) of Article 2(1), the Agency shall, where applicable and as specified in the Chicago Convention or the Annexes thereto, carry out on behalf of Member States the functions and tasks of the state of design, manufacture or registry, when those functions and tasks are related to design certification and mandatory continuing airworthiness information. To that end, it shall in particular:
(a) for each design of a product and equipment to control unmanned aircraft remotely for which a type certificate, a restricted type certificate, a change to a type certificate or to a restricted type certificate, including a supplemental type certificate, an approval of repair design, or an approval of operational suitability data has been applied for in accordance with Article 11 or Article 56(1) establish and notify to the applicant the certification basis;
(b) for each design of a part or non-installed equipment for which a certificate has been applied for in accordance with Article 12, 13 or Article 56(1) respectively, establish and notify to the applicant the certification basis;
(c) for aircraft for which a permit to fly has been applied for in accordance with point (b) of the first subparagraph of Article 18(2) or Article 56(1), issue the approval for associated flight conditions related to the design;
(d) establish and make available the airworthiness and environmental compatibility specifications applicable to the design of products, parts, non-installed equipment and equipment to control unmanned aircraft remotely which are subject to a declaration in accordance with point (a) of Article 18(1) or Article 56(5);
(e) be responsible for the tasks related to certification, oversight and enforcement in accordance with Article 62(2) with respect to the type certificates, restricted type certificates, certificates of changes, including supplemental type certificates, and approvals of repair designs and approvals of operational suitability data for the design of products in accordance with Article 11, point (b) of Article 18(1) or Article 56(1);
(f) be responsible for the tasks related to certification, oversight and enforcement in accordance with Article 62(2) with respect to the certificates for the design of parts, for non-installed equipment and equipment to control unmanned aircraft remotely in accordance with Articles 12, 13 and 56(1);
(g) issue the appropriate environmental data sheets on the design of products which it certifies in accordance with Articles 11 and 56(1);
(h) ensure the continuing airworthiness functions associated with the design of products, the design of parts, non-installed equipment and equipment to control unmanned aircraft remotely it has certified and in respect of which it performs oversight, including reacting without undue delay to a safety or security problem and issuing and disseminating the applicable mandatory information.
2. The Agency shall be responsible for the tasks related to certification, oversight and enforcement in accordance with Article 62(2) with respect to:
(a) the approvals of and the declarations made by the organisations responsible for the design of products, parts, non-installed equipment and equipment to control unmanned aircraft remotely, in accordance with Article 15(1), point (g) of Article 19(1) and Article 56(1) and (5);
(b) the approvals of and the declarations made by the organisations responsible for the production, maintenance and continuing airworthiness management of products, parts, non-installed equipment and equipment to control unmanned aircraft remotely and by the organisations involved in the training of personnel responsible for the release of a product, part, non-installed equipment or equipment to control unmanned aircraft remotely after maintenance in accordance with Article 15, point (g) of Article 19(1) and Article 56(1) and (5), where those organisations have their principal place of business outside the territories for which Member States are responsible under the Chicago Convention.
3. The Agency shall be responsible for the tasks related to oversight and enforcement in accordance with Article 62(2) with respect to the declarations made by organisations, in accordance with point (a) of Article 18(1) and Article 56(5) and concerning the compliance of a design of a product, part, non-installed equipment or equipment to control unmanned aircraft remotely with detailed technical specifications.""",
    "parent_section": None,
    "hierarchy_path": ["Article 77"],
    "metadata": {"article_number": "77", "chapter": None},
}


def main():
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from quiz_gen.agents.workflow import QuizGenerationWorkflow
    from quiz_gen.agents.config import AgentConfig

    print("=" * 70)
    print("Testing Multi-Agent Workflow with Article 77")
    print("=" * 70)
    print()

    print(f"Article: {ARTICLE_77_CHUNK['title']}")
    print(f"Content preview: {ARTICLE_77_CHUNK['content'][:200]}...\n")

    print("Initializing configuration...")
    config = AgentConfig(temperature=0.7, auto_accept_valid=False, verbose=True)
    try:
        config.validate()
        print("✓ Configuration valid\n")
    except ValueError as e:
        print(
            f"✗ Configuration error: {e}\nPlease set environment variables:\n  export OPENAI_API_KEY='your-key'\n  export ANTHROPIC_API_KEY='your-key'"
        )
        return

    print("Initializing workflow...")
    workflow = QuizGenerationWorkflow(config)
    print("✓ Workflow initialized\n")

    print("Running multi-agent workflow...")
    print("-" * 70)
    result = workflow.run(ARTICLE_77_CHUNK)
    print("-" * 70)
    print()

    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    print(f"All Valid: {result.get('all_valid', False)}\n")
    if result.get("validation_results"):
        for i, val_result in enumerate(result["validation_results"], 1):
            print(f"Validation {i}:")
            print(f"  Valid: {val_result.get('valid', False)}")
            print(f"  Score: {val_result.get('score', 0)}/10")
            if val_result.get("issues"):
                print(f"  Issues: {', '.join(val_result['issues'])}")
        print()
    print(f"Judge Decision: {result.get('judge_decision', 'N/A')}")
    print(f"Judge Reasoning: {result.get('judge_reasoning', 'N/A')}")

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

    if result.get("errors"):
        print("=" * 70)
        print("ERRORS")
        print("=" * 70)
        for error in result["errors"]:
            print(f"  • {error}")
        print()

    output_dir = Path("data/quizzes/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "article_77_quiz.json"

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

    print(f"Result saved to: {output_file}\n")


if __name__ == "__main__":
    main()
