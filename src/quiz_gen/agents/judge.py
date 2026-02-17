"""
Judge Agent
Reviews refined Q&As and makes final accept/reject decisions
"""

from anthropic import Anthropic
import cohere
from google import genai
from google.genai import types
from mistralai import Mistral
from openai import OpenAI
import os
import json
from typing import Dict, Optional


class Judge:
    """Makes final accept/reject decisions on refined quiz questions"""

    SYSTEM_PROMPT = """You are an expert judge for a multi-agent quiz generation workflow. You receive quiz questions (0-2 questions: conceptual and/or practical) AND their validation results from a strict validator.

Your job is to make the FINAL decision on which questions should be accepted and shown to the end user. 

IMPORTANT: Questions have ALREADY been refined by a separate refiner agent to fix validation issues. 
Your job is NOT to refine - only to ACCEPT or REJECT.

You may receive:
- Both conceptual and practical questions
- Only a conceptual question (if practical generation failed)
- Only a practical question (if conceptual generation failed)
- No questions (if both generations failed)

For the questions you receive, you may:
- Accept both questions if both are high quality and meet requirements
- Accept only the conceptual question if only it is acceptable
- Accept only the practical question if only it is acceptable  
- Reject both if neither is suitable
- If only one question was generated and it's valid, ACCEPT IT (don't reject just because the other is missing)

Consider:
- Validator's pass/fail, issues, and 10-point score for each question (these are FINAL results after refinement and re-validation)
- Accuracy: Does it correctly reflect the regulation?
- Distinctiveness: If both exist, do they test different skills?
- Difficulty: Is it appropriate for certification level?

IMPORTANT DESIGN PRINCIPLE:
- Questions should NOT reference regulation names, annex numbers, article numbers, or section identifiers in the question text
- References in explanations are fine, but question text should be standalone

Your final output must be a single JSON object with the following structure:
{
    "decision": "accept_both|accept_conceptual|accept_practical|reject_both",
    "reasoning": "Brief explanation of your decision, referencing validator results and score(s)"
}

Do NOT include the questions in your output - only your decision and reasoning.
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
        self.provider = provider or "anthropic"
        self.model = model or "claude-sonnet-4-20250514"
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

    def judge(
        self,
        conceptual_qa: Dict,
        practical_qa: Dict,
        validation_results: list,
        chunk: Dict,
    ) -> Dict:
        """Make final accept/reject decision on refined Q&As, using validator results"""
        
        # Build prompt based on which questions exist
        user_prompt = f"""Original Content:
{json.dumps(chunk, indent=2)}

"""
        
        if conceptual_qa:
            user_prompt += f"""CONCEPTUAL Question:
{json.dumps(conceptual_qa, indent=2)}

"""
        else:
            user_prompt += """CONCEPTUAL Question: None (generation failed)

"""
            
        if practical_qa:
            user_prompt += f"""PRACTICAL Question:
{json.dumps(practical_qa, indent=2)}

"""
        else:
            user_prompt += """PRACTICAL Question: None (generation failed)

"""
        
        user_prompt += f"""VALIDATION RESULTS (from strict validator):
{json.dumps(validation_results, indent=2)}

"""
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens or 4096,
                messages=[{"role": "user", "content": user_prompt}],
                system=self.SYSTEM_PROMPT,
            )
            # Extract JSON from response
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
            # Extract JSON from Cohere response
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
        result["judge_model"] = self.model

        return result
