#!/usr/bin/env python3
"""
Test multi-agent workflow with ANNEX IX of Regulation (EU) 2018/1139
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



ANNEX_IX = {
    "section_type": "annex",
    "number": "ix",
    "title": "Essential requirements for unmanned aircraft",
    "content": """Essential requirements for unmanned aircraft
1.   ESSENTIAL REQUIREMENTS FOR THE DESIGN, PRODUCTION, MAINTENANCE AND OPERATION OF UNMANNED AIRCRAFT
1.1.   The operator and the remote pilot of an unmanned aircraft must be aware of the applicable Union and national rules relating to the intended operations, in particular with regard to safety, privacy, data protection, liability, insurance, security and environmental protection. The operator and the remote pilot must be able to ensure the safety of operation and safe separation of the unmanned aircraft from people on the ground and from other airspace users. This includes good knowledge of the operating instructions provided by the producer, of safe and environmentally-friendly use of unmanned aircraft in the airspace, and of all relevant functionalities of the unmanned aircraft and applicable rules of the air and ATM/ANS procedures.
1.2.   An unmanned aircraft must be designed and constructed so that it is fit for its intended function, and can be operated, adjusted and maintained without putting persons at risk.
1.3.   If necessary to mitigate risks pertaining to safety, privacy, protection of personal data, security or the environment, arising from the operation, the unmanned aircraft must have the corresponding and specific features and functionalities which take into account the principles of privacy and protection of personal data by design and by default. According to the needs those features and functionalities must ensure easy identification of the aircraft and of the nature and purpose of the operation; and must ensure that applicable limitations, prohibitions or conditions be complied with, in particular with respect to the operation in particular geographical zones, beyond certain distances from the operator or at certain altitudes.
1.4.   The organisation responsible for the production or for the marketing of the unmanned aircraft must provide information to the operator of an unmanned aircraft and, where relevant, to the maintenance organisation on the kind of operations for which the unmanned aircraft is designed together with the limitations and information necessary for its safe operation, including operational and environmental performance, airworthiness limitations and emergency procedures. This information shall be given in a clear, consistent and unambiguous manner. The operational capabilities of unmanned aircraft that can be used in operations that do not require a certificate or declaration must allow the possibility to introduce limitations which meet airspace rules applicable to such operations..""",
    "parent_section": None,
    "hierarchy_path": ["annex ix"],
    "metadata": {
        "article_number": "ix",
        "chapter": None
    }
}


def main():
    """Test workflow with ANNEX IX"""
    
    print("="*70)
    print("Testing Multi-Agent Workflow with ANNEX IX")
    print("="*70)
    print()
    
    # Display article info
    print(f"Annex: {ANNEX_IX['title']}")
    print(f"Content preview: {ANNEX_IX['content'][:200]}...")
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
    
    # Run workflow for ANNEX X
    print("Running multi-agent workflow...")
    print("-"*70)
    result = workflow.run(ANNEX_IX)
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
    output_file = output_dir / "annex_ix_quiz.json"
    
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