#!/usr/bin/env python3
"""
LangGraph Workflow for Multi-Agent Quiz Generation
Orchestrates: Conceptual Gen (OpenAI) || Practical Gen (Claude) -> Judge (Claude) -> Validator (OpenAI) -> Human
"""

from typing import TypedDict, Optional, List, Dict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import json
from pathlib import Path

from quiz_gen.agents.conceptual_generator import ConceptualGenerator
from quiz_gen.agents.practical_generator import PracticalGenerator
from quiz_gen.agents.judge import Judge
from quiz_gen.agents.validator import Validator
from quiz_gen.agents.config import AgentConfig


# State definition
class QuizGenerationState(TypedDict):
    """State for the quiz generation workflow"""
    # Input
    chunk: Dict
    improvement_feedback: Optional[str]
    
    # Generated Q&As
    conceptual_qa: Optional[Dict]
    practical_qa: Optional[Dict]
    
    # Judge output
    judge_decision: Optional[str]
    judge_reasoning: Optional[str]
    judged_qas: Optional[Dict]
    
    # Validation results
    validation_results: Optional[List[Dict]]
    all_valid: Optional[bool]
    
    # Final output
    final_questions: List[Dict]  # Removed operator.add to prevent duplicates
    
    # Human feedback (for next iteration)
    human_feedback: Optional[str]
    human_action: Optional[str]  # "accept", "reject", "improve"
    
    # Status
    current_step: str
    errors: List[str]  # Removed operator.add to prevent duplicates


class QuizGenerationWorkflow:
    """LangGraph workflow for quiz generation"""
    
    def __init__(self, config: AgentConfig = None):
        """Initialize workflow with agent configuration"""
        self.config = config or AgentConfig()
        self.config.validate()
        
        # Initialize agents
        self.conceptual_gen = ConceptualGenerator(
            api_key=self.config.openai_api_key,
            api_base=self.config.openai_api_base
        )
        self.practical_gen = PracticalGenerator(
            api_key=self.config.anthropic_api_key,
            api_base=self.config.anthropic_api_base
        )
        self.judge = Judge(
            api_key=self.config.anthropic_api_key,
            api_base=self.config.anthropic_api_base
        )
        self.validator = Validator(
            api_key=self.config.openai_api_key,
            api_base=self.config.openai_api_base
        )
        
        # Build graph
        self.graph = self._build_graph()
        self.app = self.graph.compile(checkpointer=MemorySaver())
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(QuizGenerationState)

        # Nodes
        workflow.add_node("parallel_start", lambda state: {})  # dummy node for parallel fan-out
        workflow.add_node("generate_conceptual", self._generate_conceptual)
        workflow.add_node("generate_practical", self._generate_practical)
        workflow.add_node("validate_questions", self._validate_questions)
        workflow.add_node("judge_questions", self._judge_questions)
        workflow.add_node("await_human_feedback", self._await_human_feedback)

        # Entry point
        workflow.set_entry_point("parallel_start")

        # Fan-out
        workflow.add_edge("parallel_start", "generate_conceptual")
        workflow.add_edge("parallel_start", "generate_practical")

        # Fan-in: after both generators, go to validation
        workflow.add_edge("generate_conceptual", "validate_questions")
        workflow.add_edge("generate_practical", "validate_questions")

        # Sequential: validation -> judge -> human feedback
        workflow.add_edge("validate_questions", "judge_questions")
        workflow.add_edge("judge_questions", "await_human_feedback")

        # Conditional loop
        workflow.add_conditional_edges(
            "await_human_feedback",
            self._route_after_human_feedback,
            {
                "accept": END,
                "reject": END,
                "improve": "parallel_start",
            },
        )

        return workflow
    
    def _validate_questions(self, state: QuizGenerationState) -> QuizGenerationState:
        """Validate both Q&As before judging"""
        try:
            print("✅ Validating questions...")
            state["current_step"] = "validate_questions"
            # Collect Q&As to validate
            questions_to_validate = []
            if state.get("conceptual_qa"):
                questions_to_validate.append(state["conceptual_qa"])
            if state.get("practical_qa"):
                questions_to_validate.append(state["practical_qa"])
            # Validate each question
            validation_results = self.validator.validate_batch(
                qas=questions_to_validate,
                chunk=state["chunk"]
            )
            state["validation_results"] = validation_results
            state["all_valid"] = all(v["valid"] for v in validation_results)
            # Store all individually valid questions (for legacy output)
            state["final_questions"] = [q for q, v in zip(questions_to_validate, validation_results) if v["valid"]]
            for i, result in enumerate(validation_results, 1):
                status = "✓ VALID" if result["valid"] else "✗ INVALID"
                print(f"  Question {i}: {status} (score: {result['score']}/8)")
                print(f"  Question {i}: {status} (score: {result['score']}/10)")
                if result["issues"]:
                    print(f"    Issues: {', '.join(result['issues'])}")
        except Exception as e:
            errors = state.get("errors", [])
            errors.append(f"Validation error: {str(e)}")
            state["errors"] = errors
            print(f"✗ Error: {e}")
        return state

    def _generate_conceptual(self, state: QuizGenerationState):
        print("💡 Generating conceptual question...")

        try:
            conceptual_qa = self.conceptual_gen.generate(
                chunk=state["chunk"],
                improvement_feedback=state.get("improvement_feedback")
            )

            print(f"✓ Conceptual question generated: {conceptual_qa.get('question', '')[:100]}...")

            return {
                "conceptual_qa": conceptual_qa
            }

        except Exception as e:
            return {
                "errors": [f"Conceptual generation error: {str(e)}"]
            }

    
    def _generate_practical(self, state: QuizGenerationState):
        print("⚙️ Generating practical question...")

        try:
            practical_qa = self.practical_gen.generate(
                chunk=state["chunk"],
                improvement_feedback=state.get("improvement_feedback")
            )

            print(f"✓ Practical question generated: {practical_qa.get('question', '')[:100]}...")

            return {
                "practical_qa": practical_qa
            }

        except Exception as e:
            return {
                "errors": [f"Practical generation error: {str(e)}"]
            }

    
    def _validate_questions(self, state: QuizGenerationState) -> QuizGenerationState:
        """Validate both Q&As before judging"""
        try:
            print("📝 Validating questions...")
            state["current_step"] = "validate_questions"
            # Collect Q&As to validate
            questions_to_validate = []
            if state.get("conceptual_qa"):
                questions_to_validate.append(state["conceptual_qa"])
            if state.get("practical_qa"):
                questions_to_validate.append(state["practical_qa"])
            # Validate each question
            validation_results = self.validator.validate_batch(
                qas=questions_to_validate,
                chunk=state["chunk"]
            )
            state["validation_results"] = validation_results
            state["all_valid"] = all(v["valid"] for v in validation_results)
            # Store all individually valid questions (for legacy output)
            state["final_questions"] = [q for q, v in zip(questions_to_validate, validation_results) if v["valid"]]
            for i, result in enumerate(validation_results, 1):
                status = "✓ VALID" if result["valid"] else "✗ INVALID"
                print(f"  Question {i}: {status} (score: {result['score']}/8)")
                print(f"  Question {i}: {status} (score: {result['score']}/10)")
                if result["issues"]:
                    print(f"    Issues: {', '.join(result['issues'])}")
        except Exception as e:
            errors = state.get("errors", [])
            errors.append(f"Validation error: {str(e)}")
            state["errors"] = errors
            print(f"✗ Error: {e}")
        return state


    def _judge_questions(self, state: QuizGenerationState):
        print("⚖️ Judging questions...")
        try:
            judge_result = self.judge.judge(
                conceptual_qa=state.get("conceptual_qa"),
                practical_qa=state.get("practical_qa"),
                validation_results=state.get("validation_results"),
                chunk=state["chunk"]
            )
            print(f"✓ Judge decision: {judge_result['decision']}")
            print(f"  Reasoning: {judge_result['reasoning']}")
            # Use judge questions array for final_questions
            final_questions = judge_result.get("questions", [])
            # Ensure generator and model metadata are present
            for q in final_questions:
                if "generator" not in q or not q["generator"]:
                    if q.get("focus") == "conceptual":
                        q["generator"] = "conceptual"
                        q["model"] = getattr(self.conceptual_gen, "model", "gpt-4o")
                    elif q.get("focus") == "practical":
                        q["generator"] = "practical"
                        q["model"] = getattr(self.practical_gen, "model", "claude-sonnet-4-20250514")
            state["final_questions"] = final_questions
            state["judge_decision"] = judge_result["decision"]
            state["judge_reasoning"] = judge_result["reasoning"]
            state["judged_qas"] = final_questions
            state["current_step"] = "judge_questions"
            return state
        except Exception as e:
            errors = state.get("errors", [])
            errors.append(f"Judge error: {str(e)}")
            state["errors"] = errors
            print(f"✗ Error: {e}")
            return state

    
    
    def _await_human_feedback(self, state: QuizGenerationState) -> QuizGenerationState:
        """Placeholder for human feedback - will be implemented in UI"""
        print("\n👤 Awaiting human feedback...")
        print("   (This will be handled by UI)")
        
        state["current_step"] = "await_human_feedback"
        
        # For now, auto-accept if all valid
        if state.get("all_valid"):
            state["human_action"] = "accept"
            print("   Auto-accepting (all questions valid)")
        else:
            state["human_action"] = "reject"
            print("   Auto-rejecting (validation failed)")
        
        return state
    
    def _route_after_human_feedback(self, state: QuizGenerationState) -> str:
        """Route based on human feedback"""
        action = state.get("human_action", "reject")
        
        if action == "accept":
            return "accept"
        elif action == "improve":
            # Set improvement feedback for next iteration
            return "improve"
        else:
            return "reject"
    
    def run(self, chunk: Dict, improvement_feedback: Optional[str] = None) -> Dict:
        """Run the workflow for a single chunk"""
        
        initial_state = {
            "chunk": chunk,
            "improvement_feedback": improvement_feedback,
            "conceptual_qa": None,
            "practical_qa": None,
            "validation_results": None,
            "all_valid": None,
            "judge_decision": None,
            "judge_reasoning": None,
            "judged_qas": None,
            "final_questions": [],
            "human_feedback": None,
            "human_action": None,
            "current_step": "init",
            "errors": []
        }
        
        print(f"\n{'='*70}")
        print(f"Processing chunk: {chunk.get('title', 'Unknown')}")
        print(f"{'='*70}\n")
        
        # Run workflow
        config = {"configurable": {"thread_id": chunk.get("number", "1")}}
        final_state = self.app.invoke(initial_state, config)
        
        return final_state
    
    def run_batch(self, chunks: List[Dict], save_output: bool = True, 
                  output_dir: str = "data/quizzes") -> List[Dict]:
        """Run workflow for multiple chunks"""
        
        results = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n{'#'*70}")
            print(f"# Chunk {i}/{len(chunks)}")
            print(f"{'#'*70}")
            
            result = self.run(chunk)
            results.append(result)
            
            if save_output and result.get("final_questions"):
                self._save_result(result, output_dir)
        
        return results
    
    def _save_result(self, result: Dict, output_dir: str):
        """Save generated questions to file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        chunk_id = result["chunk"].get("number", "unknown")
        filename = f"quiz_{chunk_id}.json"
        filepath = output_path / filename
        
        output_data = {
            "chunk": result["chunk"],
            "questions": result["final_questions"],
            "judge_decision": result.get("judge_decision"),
            "validation_results": result.get("validation_results"),
            "errors": result.get("errors", [])
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved to: {filepath}")