#!/usr/bin/env python3
"""
LangGraph Workflow for Multi-Agent Quiz Generation
Orchestrates: Conceptual Gen (OpenAI) || Practical Gen (Claude) -> Judge (Claude) -> Validator (OpenAI) -> Human
"""

from typing import TypedDict, Optional, List, Dict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import json
from pathlib import Path

from quiz_gen.agents.conceptual_generator import ConceptualGenerator
from quiz_gen.agents.practical_generator import PracticalGenerator
from quiz_gen.agents.judge import Judge
from quiz_gen.agents.validator import Validator
from quiz_gen.agents.refiner import Refiner
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
        conceptual_key, conceptual_base = self._get_provider_config(
            self.config.conceptual_provider
        )
        practical_key, practical_base = self._get_provider_config(
            self.config.practical_provider
        )
        judge_key, judge_base = self._get_provider_config(self.config.judge_provider)
        validator_key, validator_base = self._get_provider_config(
            self.config.validator_provider
        )
        refiner_key, refiner_base = self._get_provider_config(
            self.config.refiner_provider
        )

        self.conceptual_gen = ConceptualGenerator(
            api_key=conceptual_key,
            api_base=conceptual_base,
            provider=self.config.conceptual_provider,
            model=self.config.conceptual_model,
            max_tokens=self.config.anthropic_max_tokens if self.config.conceptual_provider == "anthropic" else None,
        )
        self.practical_gen = PracticalGenerator(
            api_key=practical_key,
            api_base=practical_base,
            provider=self.config.practical_provider,
            model=self.config.practical_model,
            max_tokens=self.config.anthropic_max_tokens if self.config.practical_provider == "anthropic" else None,
        )
        self.judge = Judge(
            api_key=judge_key,
            api_base=judge_base,
            provider=self.config.judge_provider,
            model=self.config.judge_model,
            max_tokens=self.config.anthropic_max_tokens if self.config.judge_provider == "anthropic" else None,
        )
        self.validator = Validator(
            api_key=validator_key,
            api_base=validator_base,
            provider=self.config.validator_provider,
            model=self.config.validator_model,
            max_tokens=self.config.anthropic_max_tokens if self.config.validator_provider == "anthropic" else None,
        )
        self.refiner = Refiner(
            api_key=refiner_key,
            api_base=refiner_base,
            provider=self.config.refiner_provider,
            model=self.config.refiner_model,
            max_tokens=self.config.anthropic_max_tokens if self.config.refiner_provider == "anthropic" else None,
        )

        # Build graph
        self.graph = self._build_graph()
        self.app = self.graph.compile(checkpointer=MemorySaver())

    def _get_provider_config(self, provider: str):
        if provider == "anthropic":
            return self.config.anthropic_api_key, self.config.anthropic_api_base
        if provider == "cohere":
            return self.config.cohere_api_key, None
        if provider == "mistral":
            return self.config.mistral_api_key, self.config.mistral_api_base
        if provider in {"gemini", "google"}:
            return self.config.gemini_api_key, self.config.gemini_api_base
        return self.config.openai_api_key, self.config.openai_api_base

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(QuizGenerationState)

        # Nodes
        workflow.add_node(
            "parallel_start", lambda state: {}
        )  # dummy node for parallel fan-out
        workflow.add_node("generate_conceptual", self._generate_conceptual)
        workflow.add_node("generate_practical", self._generate_practical)
        workflow.add_node("validate_questions", self._validate_questions)
        workflow.add_node("refine_questions", self._refine_questions)
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

        # Sequential: validation -> refiner -> judge -> human feedback
        workflow.add_edge("validate_questions", "refine_questions")
        workflow.add_edge("refine_questions", "judge_questions")
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

    def _generate_conceptual(self, state: QuizGenerationState):
        if self.config.verbose:
            print("  → Generating conceptual question...")
        try:
            conceptual_qa = self.conceptual_gen.generate(
                chunk=state["chunk"],
                improvement_feedback=state.get("improvement_feedback"),
            )
            return {"conceptual_qa": conceptual_qa}
        except Exception as e:
            return {"errors": [f"Conceptual generation error: {str(e)}"]}

    def _generate_practical(self, state: QuizGenerationState):
        if self.config.verbose:
            print("  → Generating practical question...")
        try:
            practical_qa = self.practical_gen.generate(
                chunk=state["chunk"],
                improvement_feedback=state.get("improvement_feedback"),
            )
            return {"practical_qa": practical_qa}
        except Exception as e:
            return {"errors": [f"Practical generation error: {str(e)}"]}

    def _validate_questions(self, state: QuizGenerationState) -> QuizGenerationState:
        """Validate both Q&As before judging"""
        if self.config.verbose:
            print("  → Validating questions...")
        try:
            state["current_step"] = "validate_questions"
            # Collect Q&As to validate (only non-None questions)
            questions_to_validate = []
            question_types = []
            if state.get("conceptual_qa"):
                questions_to_validate.append(state["conceptual_qa"])
                question_types.append("conceptual")
            if state.get("practical_qa"):
                questions_to_validate.append(state["practical_qa"])
                question_types.append("practical")
            
            # Only validate if we have questions
            if questions_to_validate:
                # Validate each question
                validation_results = self.validator.validate_batch(
                    qas=questions_to_validate, chunk=state["chunk"]
                )
                # Add question_type metadata to each validation result
                for i, val_result in enumerate(validation_results):
                    val_result["question_type"] = question_types[i]
                
                state["validation_results"] = validation_results
                state["all_valid"] = all(v["valid"] for v in validation_results)
                # Store all individually valid questions (for legacy output)
                state["final_questions"] = [
                    q
                    for q, v in zip(questions_to_validate, validation_results)
                    if v["valid"]
                ]
            else:
                # No questions to validate
                state["validation_results"] = []
                state["all_valid"] = False
                state["final_questions"] = []
        except Exception as e:
            errors = state.get("errors", [])
            errors.append(f"Validation error: {str(e)}")
            state["errors"] = errors
        return state

    def _refine_questions(self, state: QuizGenerationState) -> QuizGenerationState:
        """Refine questions based on validation results"""
        if self.config.verbose:
            print("  → Refining questions...")
        try:
            state["current_step"] = "refine_questions"
            
            # Collect questions and their validation results
            questions_to_refine = []
            validation_results = state.get("validation_results", [])
            
            if state.get("conceptual_qa"):
                questions_to_refine.append(state["conceptual_qa"])
            if state.get("practical_qa"):
                questions_to_refine.append(state["practical_qa"])
            
            # Refine each question
            refined_questions = self.refiner.refine_batch(
                qas=questions_to_refine,
                validation_results=validation_results,
                chunk=state["chunk"]
            )
            
            # Store refined questions back in state
            if len(refined_questions) > 0 and state.get("conceptual_qa"):
                state["refined_conceptual_qa"] = refined_questions[0]
            
            if len(refined_questions) > 1 and state.get("practical_qa"):
                state["refined_practical_qa"] = refined_questions[1]
            elif len(refined_questions) == 1 and state.get("practical_qa") and not state.get("conceptual_qa"):
                # Edge case: only practical question exists
                state["refined_practical_qa"] = refined_questions[0]
                
        except Exception as e:
            errors = state.get("errors", [])
            errors.append(f"Refinement error: {str(e)}")
            state["errors"] = errors
        return state

    def _judge_questions(self, state: QuizGenerationState):
        if self.config.verbose:
            print("  → Judging questions...")
        try:
            # Use refined questions if available, otherwise use originals
            conceptual_qa = state.get("refined_conceptual_qa") or state.get("conceptual_qa")
            practical_qa = state.get("refined_practical_qa") or state.get("practical_qa")
            
            judge_result = self.judge.judge(
                conceptual_qa=conceptual_qa,
                practical_qa=practical_qa,
                validation_results=state.get("validation_results"),
                chunk=state["chunk"],
            )
            
            # Store judge decision
            state["judge_decision"] = judge_result["decision"]
            state["judge_reasoning"] = judge_result["reasoning"]
            state["current_step"] = "judge_questions"
            
            # Construct final_questions based on judge's decision
            final_questions = []
            decision = judge_result["decision"]
            
            if decision == "accept_both":
                final_questions = [conceptual_qa, practical_qa]
            elif decision == "accept_conceptual":
                final_questions = [conceptual_qa]
            elif decision == "accept_practical":
                final_questions = [practical_qa]
            # reject_both: final_questions remains empty []
            
            # Add metadata to accepted questions
            for q in final_questions:
                # Ensure generator and model metadata are present
                if "generator" not in q or not q["generator"]:
                    if q.get("focus") == "conceptual":
                        q["generator"] = "conceptual"
                        q["model"] = getattr(self.conceptual_gen, "model", "gpt-4o")
                    elif q.get("focus") == "practical":
                        q["generator"] = "practical"
                        q["model"] = getattr(
                            self.practical_gen, "model", "claude-sonnet-4-20250514"
                        )
                # Automatically populate source_reference from chunk hierarchy_path
                hierarchy = state["chunk"].get("hierarchy_path", [])
                q["source_reference"] = " > ".join(hierarchy) if hierarchy else "Unknown"
            
            state["final_questions"] = final_questions
            state["judged_qas"] = final_questions
            return state
        except Exception as e:
            errors = state.get("errors", [])
            errors.append(f"Judge error: {str(e)}")
            state["errors"] = errors
            return state

    def _await_human_feedback(self, state: QuizGenerationState) -> QuizGenerationState:
        """Placeholder for human feedback - will be implemented in UI"""
        state["current_step"] = "await_human_feedback"

        # For now, auto-accept if all valid
        if state.get("all_valid"):
            state["human_action"] = "accept"
        else:
            state["human_action"] = "reject"

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
            "refined_conceptual_qa": None,
            "refined_practical_qa": None,
            "judge_decision": None,
            "judge_reasoning": None,
            "judged_qas": None,
            "final_questions": [],
            "human_feedback": None,
            "human_action": None,
            "current_step": "init",
            "errors": [],
        }

        # Run workflow
        config = {"configurable": {"thread_id": chunk.get("number", "1")}}
        final_state = self.app.invoke(initial_state, config)

        return final_state

    def run_batch(
        self,
        chunks: List[Dict],
        save_output: bool = True,
        output_dir: str = "data/quizzes",
    ) -> List[Dict]:
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
            "errors": result.get("errors", []),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved to: {filepath}")
