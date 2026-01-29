"""
Validator Agent (OpenAI)
Checks formal requirements and structure compliance
"""

from openai import OpenAI
import os
import json
from typing import Dict, List, Optional


class Validator:
    """Validates quiz question format and structure using OpenAI"""
    
    SYSTEM_PROMPT = """You are a strict validator for a multi-agent quiz generation workflow. Your job is to pre-screen each quiz question for structural and content compliance BEFORE it is shown to the judge or end user.

For EACH question, check ALL these requirements:

STRUCTURAL REQUIREMENTS:
1. Exactly 4 multiple choice options (A, B, C, D)
2. Exactly one correct answer marked
3. Explanation for ALL 4 options (A, B, C, D)
4. Each explanation is 1-2 sentences maximum
5. Question text is clear and complete

CONTENT REQUIREMENTS:
6. Correct answer explanation confirms why it's right
7. Wrong answer explanations explain why they're wrong (act as hints)
8. All options are plausible (not obviously wrong)
9. Question is unambiguous
10. Based strictly on provided regulation content

Output format (JSON):
{
    "valid": true/false,  // Should this question be shown to the judge/end user?
    "issues": ["List of any problems found"],
    "warnings": ["List of minor issues or suggestions"],
    "checks_passed": {
        "has_4_options": true/false,
        "has_correct_answer": true/false,
        "has_all_explanations": true/false,
        "explanations_concise": true/false,
        "question_clear": true/false,
        "options_plausible": true/false,
        "unambiguous": true/false,
        "regulation_based": true/false
    },
    "score": 8  // Number of checks passed out of 8
}

Be strict but fair. Mark as invalid only if critical requirements are missing. Your output will be used by the judge agent to make the final decision on which questions to accept for the end user.
"""

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """Initialize OpenAI client"""
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=api_base
        )
        self.model = "gpt-4o"
    
    def validate(self, qa: Dict, chunk: Dict) -> Dict:
        """Validate a single Q&A against requirements"""
        
        user_prompt = f"""Original Regulation Content:
{json.dumps(chunk, indent=2)}

Quiz Question to Validate:
{json.dumps(qa, indent=2)}

Validate this question against all requirements.
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["validator_model"] = self.model
        
        return result
    
    def validate_batch(self, qas: List[Dict], chunk: Dict) -> List[Dict]:
        """Validate multiple Q&As"""
        return [self.validate(qa, chunk) for qa in qas]