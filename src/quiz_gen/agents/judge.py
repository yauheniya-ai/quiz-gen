"""
Judge Agent
Reviews both generated Q&As and either accepts, refines, or unifies them
"""

from anthropic import Anthropic
from google import genai
from google.genai import types
from mistralai import Mistral
from openai import OpenAI
import os
import json
from typing import Dict, Optional


class Judge:
    """Judges and refines quiz questions"""

    SYSTEM_PROMPT = """You are an expert judge for a multi-agent quiz generation workflow. You receive TWO quiz questions (one conceptual, one practical) AND their validation results from a strict validator.

Your job is to make the FINAL decision on which questions should be accepted and shown to the end user. For each question, you may:
- Accept both questions if both are high quality and meet requirements
- Accept only one if only one is valid and high quality
- Reject both if neither is suitable
- Refine a question if the validator found issues that can be reasonably amended (e.g., minor clarity, plausibility, or explanation problems)

You MUST use the validator's results as a primary filter. 
The validator ranks each question on 10 criteria (score out of 10). 
If a question does not meet all requirements but can be improved, you should refine it. 
When refining:
- Fix factual errors
- Improve clarity
- Make wrong answers more plausible
- Enhance explanations
- Ensure proper difficulty level
If a question is fundamentally flawed, reject it. 

Consider:
- Validator's pass/fail, issues, and 10-point score for each question
- Accuracy: Does it correctly reflect the regulation?
- Distinctiveness: Do the two questions test different skills?
- Difficulty: Is it appropriate for certification level?

Your final output must be a single JSON object with the following structure:
{
    "decision": "accept_both|accept_conceptual|accept_practical|reject_both|refine_conceptual|refine_practical|refine_both",
    "reasoning": "Brief explanation of your decision, referencing validator results and score(s)",
    "improvements_made": ["List of improvements if refined"],
    "questions": [
        {
            "question": "The question text",
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
            "source_reference": "Article X, Chapter Y",
            "difficulty": "easy|medium|hard",
            "focus": "conceptual|practical"
        }
        // ... (include both if both are accepted/refined, conceptual first)
    ]
}

The 'questions' array must contain the final, fully-formed question objects for all accepted or refined questions, 
in the order: conceptual first (if present), then practical (if present). 
If both are rejected, return an empty array. Do not include any other fields or partial objects.
You must always submit the final questions in the correct format as shown above. 
Never return partial or referenced questions—always output the full, final question object(s).
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Initialize model client"""
        self.provider = provider or "anthropic"
        self.model = model or "claude-sonnet-4-20250514"
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

    def judge(
        self,
        conceptual_qa: Dict,
        practical_qa: Dict,
        validation_results: list,
        chunk: Dict,
    ) -> Dict:
        """Judge and potentially refine both Q&As, using validator output"""
        user_prompt = f"""Original Regulation Content:
{json.dumps(chunk, indent=2)}

CONCEPTUAL Question:
{json.dumps(conceptual_qa, indent=2)}

PRACTICAL Question:
{json.dumps(practical_qa, indent=2)}

VALIDATION RESULTS (from strict validator):
{json.dumps(validation_results, indent=2)}

"""
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                messages=[{"role": "user", "content": user_prompt}],
                system=self.SYSTEM_PROMPT,
                temperature=0.5,
            )
            # Extract JSON from response
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
                    system_instruction=self.SYSTEM_PROMPT,
                    temperature=0.5,
                    max_output_tokens=3000,
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
                temperature=0.5,
                max_tokens=3000,
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
                temperature=0.5,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
        result["judge_model"] = self.model

        return result
