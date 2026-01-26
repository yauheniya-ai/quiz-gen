#!/usr/bin/env python3
"""
Test multi-agent workflow with Article 47 of Regulation (EU) 2018/1139
Simple test using chunked content directly
"""

import sys
from pathlib import Path
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from quiz_gen.agents.workflow import QuizGenerationWorkflow
from quiz_gen.agents.config import AgentConfig


# Article 47 chunk data
ARTICLE_47_CHUNK = {
    "section_type": "article",
    "number": "47",
    "title": "Article 47 - Delegated powers",
    "content": """1. For the ATM/ANS systems and ATM/ANS constituents the Commission is empowered to adopt delegated acts, in accordance with Article 128, laying down detailed rules with regard to:

(a) the conditions for establishing and notifying to an applicant the detailed specifications applicable to ATM/ANS systems and ATM/ANS constituents for the purposes of certification in accordance with Article 45(2);

(b) the conditions for issuing, maintaining, amending, limiting, suspending or revoking the certificates referred to in Article 45(2), and for the situations in which, with a view to achieving the objectives set out in Article 1 and while taking account of the nature and risk of the particular activity concerned, such certificates are to be required or declarations are to be permitted, as applicable;

(c) the privileges and responsibilities of the holders of certificates referred to in Article 45(2);

(d) the privileges and responsibilities of the organisations issuing declarations in accordance with Article 45(1) and (2);

(e) the conditions and procedures for the declaration by ATM/ANS providers, in accordance with Article 45(1), and for the situations in which, with a view to achieving the objectives set out in Article 1 and while taking account of the nature and risk of the particular activity concerned such declarations are to be required;

(f) the conditions for establishing the detailed specifications applicable to ATM/ANS systems and ATM/ANS constituents which are subject to a declaration in accordance with Article 45(1) and (2).

2. As regards the provision of ATM/ANS, the Commission is empowered to adopt delegated acts, in accordance with Article 128, to amend Annex VIII and, if applicable, Annex VII, where necessary for reasons of technical, operational or scientific developments or safety evidence related to the ATM/ANS, in order and to the extent required to achieve the objectives set out in Article 1.""",
    "parent_section": None,
    "hierarchy_path": ["Article 47"],
    "metadata": {
        "article_number": "47",
        "chapter": None
    }
}


def main():
    """Test workflow with Article 47"""
    
    print("="*70)
    print("Testing Multi-Agent Workflow with Article 47")
    print("="*70)
    print()
    
    # Display article info
    print(f"Article: {ARTICLE_47_CHUNK['title']}")
    print(f"Content preview: {ARTICLE_47_CHUNK['content'][:200]}...")
    print()
    
    # Initialize configuration
    print("Initializing configuration...")
    config = AgentConfig(
        temperature=0.7,
        auto_accept_valid=False,
        verbose=True
    )
    
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
    
    # Run workflow for Article 47
    print("Running multi-agent workflow...")
    print("-"*70)
    result = workflow.run(ARTICLE_47_CHUNK)
    print("-"*70)
    print()
    
    # Display results
    print("="*70)
    print("RESULTS")
    print("="*70)
    print()
    
    # Judge decision
    print(f"Judge Decision: {result.get('judge_decision', 'N/A')}")
    print(f"Judge Reasoning: {result.get('judge_reasoning', 'N/A')}")
    print()
    
    # Validation
    print(f"All Valid: {result.get('all_valid', False)}")
    if result.get('validation_results'):
        for i, val_result in enumerate(result['validation_results'], 1):
            print(f"\nValidation {i}:")
            print(f"  Valid: {val_result.get('valid', False)}")
            print(f"  Score: {val_result.get('score', 0)}/8")
            if val_result.get('issues'):
                print(f"  Issues: {', '.join(val_result['issues'])}")
    print()
    
    # Generated questions
    if result.get('final_questions'):
        print("="*70)
        print("GENERATED QUESTIONS")
        print("="*70)
        
        for i, question in enumerate(result['final_questions'], 1):
            print(f"\n{'─'*70}")
            print(f"Question {i} ({question.get('focus', 'unknown').upper()})")
            print(f"{'─'*70}")
            
            print(f"\n{question.get('question', 'N/A')}")
            
            print(f"\nOptions:")
            correct = question.get('correct_answer', '')
            for option, text in question.get('options', {}).items():
                marker = "✓" if option == correct else " "
                print(f"  [{marker}] {option}. {text}")
            
            print(f"\nExplanations:")
            for option, explanation in question.get('explanations', {}).items():
                marker = "✓" if option == correct else "✗"
                print(f"  {marker} {option}. {explanation}")
            
            print(f"\nMetadata:")
            print(f"  Difficulty: {question.get('difficulty', 'N/A')}")
            print(f"  Generator: {question.get('generator', 'N/A')}")
            print(f"  Model: {question.get('model', 'N/A')}")
    else:
        print("No valid questions generated")
    
    print()
    
    # Errors
    if result.get('errors'):
        print("="*70)
        print("ERRORS")
        print("="*70)
        for error in result['errors']:
            print(f"  • {error}")
        print()
    
    # Save result
    output_dir = Path("data/quizzes/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "article_47_quiz.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "chunk": result["chunk"],
            "questions": result.get("final_questions", []),
            "judge_decision": result.get("judge_decision"),
            "judge_reasoning": result.get("judge_reasoning"),
            "validation_results": result.get("validation_results"),
            "all_valid": result.get("all_valid"),
            "errors": result.get("errors", [])
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Result saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()