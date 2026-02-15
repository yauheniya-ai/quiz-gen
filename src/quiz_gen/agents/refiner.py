"""
Refiner Agent
Fixes issues identified by the validator in generated questions
"""

from anthropic import Anthropic
import cohere
from google import genai
from google.genai import types
from mistralai import Mistral
from openai import OpenAI
import os
import json
from typing import Dict, Optional, List


class Refiner:
    """Refines quiz questions based on validation feedback"""

    SYSTEM_PROMPT = """You are an expert question refiner for a multi-agent quiz generation workflow. 

Your job is to FIX issues and ADDRESS warnings identified by the validator in quiz questions. You receive:
1. The original question
2. Validation results indicating specific issues and warnings

Your responsibility:
- Fix ALL issues (critical problems) identified by the validator
- Address ALL warnings (suggestions for improvement) to enhance quality
- Preserve the original intent and focus of the question
- Maintain the question style and difficulty level
- Do NOT make unnecessary changes beyond addressing feedback

Common issues to fix:
- Options that are not plausible enough
- Explanations that don't properly hint at why wrong answers are incorrect
- Unclear or ambiguous question wording
- Missing or incomplete explanations
- Options that are too obviously wrong

Common warnings to address:
- Minor wording improvements for clarity
- Style consistency suggestions
- Enhanced explanation quality
- Better option distribution

Output format (JSON):
{
    "question": "The refined question text",
    "options": {
        "A": "First option text",
        "B": "Second option text", 
        "C": "Third option text",
        "D": "Fourth option text"
    },
    "correct_answer": "A",
    "explanations": {
        "A": "Why this is correct...",
        "B": "Why this is wrong...",
        "C": "Why this is wrong...",
        "D": "Why this is wrong..."
    },
    "difficulty": "easy|medium|hard",
    "focus": "conceptual|practical",
    "refinement_notes": "Brief description of what was fixed"
}

Guidelines:
- Make minimal changes necessary to address validator issues
- Keep the question focused on the same regulatory concept
- Ensure all 4 options remain plausible
- Make explanations clear and concise (1-2 sentences each)
- Preserve the generator's original style and approach
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ):
        """Initialize model client"""
        self.provider = provider or "openai"
        self.model = model or "gpt-4o"
        self.max_tokens = max_tokens
        if self.provider == "anthropic":
            anthropic_kwargs = {"api_key": api_key or os.getenv("ANTHROPIC_API_KEY")}
            if api_base:
                anthropic_kwargs["base_url"] = api_base
            self.client = Anthropic(**anthropic_kwargs)
        elif self.provider == "cohere":
            # Cohere uses its own SDK
            self.client = cohere.ClientV2(
                api_key=api_key or os.getenv("COHERE_API_KEY")
            )
        elif self.provider in {"google", "gemini"}:
            self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        elif self.provider == "mistral":
            self.client = Mistral(api_key=api_key or os.getenv("MISTRAL_API_KEY"))
        else:
            self.client = OpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY"), base_url=api_base
            )

    def refine(self, qa: Dict, validation_result: Dict, chunk: Dict) -> Dict:
        """Refine a question based on validation issues and warnings"""

        # Only skip refinement if perfect: valid, no warnings, no issues, score 10/10
        is_perfect = (
            validation_result.get("valid") == True
            and not validation_result.get("warnings", [])
            and not validation_result.get("issues", [])
            and validation_result.get("score") == 10
        )
        
        if is_perfect:
            qa["refinement_notes"] = "No refinement needed (perfect score, no warnings or issues)"
            return qa

        user_prompt = f"""Original Regulation Content:
{json.dumps(chunk, indent=2)}

Original Question:
{json.dumps(qa, indent=2)}

Validation Results:
Valid: {validation_result.get('valid')}
Score: {validation_result.get('score')}/10
Issues: {validation_result.get('issues', []) or 'None'}
Warnings: {validation_result.get('warnings', []) or 'None'}
Checks Failed: {json.dumps([k for k, v in validation_result.get('checks_passed', {}).items() if not v], indent=2)}

Fix the identified issues AND address the warnings to improve the question quality. Preserve the original question's intent and style. Output the refined question in JSON format.
"""

        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens or 4096,
                messages=[{"role": "user", "content": user_prompt}],
                system=self.SYSTEM_PROMPT,
            )
            content = response.content[0].text
            if "```json" in content:
                content = content.split("```json")[1].split("```", 1)[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            result = json.loads(content)
        elif self.provider == "cohere":
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
            )
            content = response.message.content[0].text
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
        
        # Preserve original metadata
        result["refiner_model"] = self.model
        result["generator"] = qa.get("generator", "unknown")
        result["model"] = qa.get("model", "unknown")
        
        return result

    def refine_batch(
        self, qas: List[Dict], validation_results: List[Dict], chunk: Dict
    ) -> List[Dict]:
        """Refine multiple questions"""
        return [
            self.refine(qa, val_result, chunk)
            for qa, val_result in zip(qas, validation_results)
        ]
