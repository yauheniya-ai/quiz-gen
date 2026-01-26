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
    
    SYSTEM_PROMPT = """You are an expert judge evaluating quiz questions for regulatory certification exams.

You receive TWO quiz questions generated from the same regulation content:
1. A CONCEPTUAL question (focused on theory/definitions)
2. A PRACTICAL question (focused on application/scenarios)

Your task is to evaluate both and decide:
- ACCEPT BOTH: If both are high quality and test different aspects
- REFINE BOTH: If both have issues that can be improved
- UNIFY: If they're too similar or you can create one superior combined question

Evaluation criteria:
1. Accuracy: Does it correctly reflect the regulation?
2. Clarity: Is the question unambiguous?
3. Quality: Are all options plausible? Are explanations clear?
4. Distinctiveness: Do the two questions test different skills?
5. Difficulty: Is it appropriate for certification level?

Output format (JSON):
{
  "decision": "accept_both|refine_both|unify",
  "reasoning": "Brief explanation of your decision",
  "output": {
    "conceptual": {...},  // Original or refined conceptual Q&A
    "practical": {...},   // Original or refined practical Q&A
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
    
    def judge(self, conceptual_qa: Dict, practical_qa: Dict, chunk: Dict) -> Dict:
        """Judge and potentially refine both Q&As"""
        
        user_prompt = f"""Original Regulation Content:
{json.dumps(chunk, indent=2)}

CONCEPTUAL Question:
{json.dumps(conceptual_qa, indent=2)}

PRACTICAL Question:
{json.dumps(practical_qa, indent=2)}

Please evaluate both questions and decide whether to accept both, refine both, or create a unified question.
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
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        result["judge_model"] = self.model
        
        return result