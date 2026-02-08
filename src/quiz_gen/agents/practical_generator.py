"""
Practical Generator Agent
Focuses on real-world application and scenario-based questions
"""

from anthropic import Anthropic
from google import genai
from google.genai import types
from mistralai import Mistral
from openai import OpenAI
import os
import json
from typing import Dict, Optional


class PracticalGenerator:
    """Generates practical quiz questions"""

    SYSTEM_PROMPT = """You are an expert quiz question generator focused on PRACTICAL APPLICATION.

Your task is to create quiz questions that test real-world scenarios, application of rules, and practical decision-making.

IMPORTANT: Do NOT reference the name or number of any regulation, annex, article, section, or official document in the question text itself. 
The question must stand alone and be fully understandable without mentioning any specific regulation or section. 
Do not use phrases like 'according to ANNEX IX', 'as stated in Article 47', or similar references in the question.

Given a regulation chunk, you must:
1. Create a realistic scenario where this regulation applies
2. Create ONE multiple-choice question with EXACTLY 4 options
3. Mark which option is correct
4. Provide a short explanation (1 sentence) for EACH option explaining why it's correct or wrong

Output format (JSON):
{
    "question": "The question text with practical scenario (no regulation or section references)",
    "options": {
        "A": "First option text",
        "B": "Second option text", 
        "C": "Third option text",
        "D": "Fourth option text"
    },
    "correct_answer": "B",
    "explanations": {
        "A": "Why this is wrong in this scenario...",
        "B": "Why this is the correct action...",
        "C": "Why this is wrong in this scenario...",
        "D": "Why this is wrong in this scenario..."
    },
    "source_reference": "Article X, Chapter Y",
    "difficulty": "easy|medium|hard",
    "focus": "practical"
}

Guidelines:
- Focus on "what should you do", "how would you apply", "in this situation"
- Create realistic scenarios relevant to the regulation topic
- Test practical decision-making and application
- Ensure scenarios are clear and unambiguous
- Keep explanations concise (one sentence each)
- Base everything strictly on the provided regulation text
- Do NOT mention any regulation, annex, article, section, or document name/number in the question text itself.
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """Initialize model client"""
        self.provider = provider or "anthropic"
        self.model = model or "claude-sonnet-4-20250514"
        self.temperature = 1.0 if temperature is None else temperature
        self.max_tokens = 2000 if max_tokens is None else max_tokens
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

    def generate(self, chunk: Dict, improvement_feedback: Optional[str] = None) -> Dict:
        """Generate a practical question from a regulation chunk"""

        user_prompt = f"""Regulation Content:
Section: {chunk.get('title', 'Unknown')}
Number: {chunk.get('number', 'N/A')}
Type: {chunk.get('section_type', 'Unknown')}
Content: {chunk.get('content', '')}

Hierarchy: {' > '.join(chunk.get('hierarchy_path', []))}
"""

        if improvement_feedback:
            user_prompt += f"\n\nIMPROVEMENT FEEDBACK FROM HUMAN:\n{improvement_feedback}\n\nPlease incorporate this feedback."

        user_prompt += "\n\nGenerate ONE practical quiz question in JSON format."

        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": user_prompt}],
                system=self.SYSTEM_PROMPT,
                temperature=self.temperature,
            )

            # Extract JSON from response
            content = response.content[0].text
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
        elif self.provider in {"google", "gemini"}:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.SYSTEM_PROMPT,
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
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
                temperature=self.temperature,
                max_tokens=self.max_tokens,
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
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
        result["generator"] = "practical"
        result["model"] = self.model

        return result
