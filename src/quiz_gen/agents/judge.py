"""
Judge Agent (Claude)
Reviews both generated Q&As and either accepts, refines, or unifies them
"""

from anthropic import Anthropic
import os
import json
from typing import Dict, Optional


class Judge:
    """Judges and refines quiz questions using Claude"""
    
    SYSTEM_PROMPT = """You are an expert judge for a multi-agent quiz generation workflow. You receive TWO quiz questions (one conceptual, one practical) AND their validation results from a strict validator.

Your job is to make the FINAL decision on which questions (0, 1, or 2) should be accepted and shown to the end user. You may:
- Accept both questions if both are high quality and meet requirements
- Accept only one if only one is valid and high quality
- Reject both if neither is suitable
- Optionally, suggest improvements or unify into a single superior question if appropriate

You MUST use the validator's results as a primary filter, but you may apply your own expert judgment for borderline cases. Consider:
1. Validator's pass/fail and issues for each question
2. Accuracy: Does it correctly reflect the regulation?
3. Clarity: Is the question unambiguous?
4. Quality: Are all options plausible? Are explanations clear?
5. Distinctiveness: Do the two questions test different skills?
6. Difficulty: Is it appropriate for certification level?

Output format (JSON):
{
    "decision": "accept_both|accept_conceptual|accept_practical|reject_both|unify",
    "reasoning": "Brief explanation of your decision, referencing validator results",
    "output": {
        "conceptual": {...},  // Only if accepted
        "practical": {...},   // Only if accepted
        "unified": {...}      // Only if decision is "unify"
    },
    "improvements_made": ["List of improvements if refined"]
}

When refining:
- Fix factual errors
- Improve clarity
- Make wrong answers more plausible
- Enhance explanations
- Ensure proper difficulty level

When unifying:
- Create one superior question that captures the best of both
- Maintain proper format with 4 options and all explanations
"""

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """Initialize Anthropic client"""
        self.client = Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-20250514"
    
    def judge(self, conceptual_qa: Dict, practical_qa: Dict, validation_results: list, chunk: Dict) -> Dict:
        """Judge and potentially refine both Q&As, using validator output"""
        user_prompt = f"""Original Regulation Content:
{json.dumps(chunk, indent=2)}

CONCEPTUAL Question:
{json.dumps(conceptual_qa, indent=2)}

PRACTICAL Question:
{json.dumps(practical_qa, indent=2)}

VALIDATION RESULTS (from strict validator):
{json.dumps(validation_results, indent=2)}

Please evaluate both questions and decide whether to accept both, refine both, or create a unified question. Use the validator's results as a primary filter, but apply your own expert judgment for borderline cases.
"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            system=self.SYSTEM_PROMPT,
            temperature=0.5
        )
        # Extract JSON from response
        content = response.content[0].text
        if "```json" in content:
            content = content.split("```json")[1].split("```", 1)[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        result["judge_model"] = self.model
        
        return result