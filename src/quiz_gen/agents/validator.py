"""
Validator Agent
Checks formal requirements and structure compliance
"""

from anthropic import Anthropic
from google import genai
from google.genai import types
from mistralai import Mistral
from openai import OpenAI
import os
import json
from typing import Dict, List, Optional


class Validator:
    """Validates quiz question format and structure"""

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
        "correct_explanation": true/false,
        "wrong_explanations_are_hints": true/false,
        "options_plausible": true/false,
        "question_unambiguous": true/false,
        "regulation_based": true/false,
    },
    "score": 10  // Number of checks passed out of 10
}

Be strict but fair. Mark as invalid only if critical requirements are missing. Your output will be used by the judge agent to make the final decision on which questions to accept for the end user.
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Initialize model client"""
        self.provider = provider or "openai"
        self.model = model or "gpt-4o"
        if self.provider == "anthropic":
            self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        elif self.provider in {"google", "gemini"}:
            self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        elif self.provider == "mistral":
            self.client = Mistral(api_key=api_key or os.getenv("MISTRAL_API_KEY"))
        else:
            self.client = OpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY"), base_url=api_base
            )

    def validate(self, qa: Dict, chunk: Dict) -> Dict:
        """Validate a single Q&A against requirements"""

        user_prompt = f"""Original Regulation Content:
{json.dumps(chunk, indent=2)}

Quiz Question to Validate:
{json.dumps(qa, indent=2)}

Validate this question against all requirements.
"""

        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": user_prompt}],
                system=self.SYSTEM_PROMPT,
            )
            content = response.content[0].text
            if "```json" in content:
                content = content.split("```json")[1].split("```", 1)[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            result = json.loads(content)
        elif self.provider in {"google", "gemini"}:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.SYSTEM_PROMPT
                ),
            )
            content = response.text or ""
            if "```json" in content:
                content = content.split("```json")[1].split("```", 1)[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            result = json.loads(content)
        elif self.provider == "mistral":
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```", 1)[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            result = json.loads(content)
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
        result["validator_model"] = self.model

        return result

    def validate_batch(self, qas: List[Dict], chunk: Dict) -> List[Dict]:
        """Validate multiple Q&As"""
        return [self.validate(qa, chunk) for qa in qas]
