"""
Conceptual Generator Agent (OpenAI)
Focuses on theoretical understanding and foundational concepts
"""

from openai import OpenAI
import os
import json
from typing import Dict, Optional


class ConceptualGenerator:
    """Generates conceptual quiz questions using OpenAI"""
    
    SYSTEM_PROMPT = """You are an expert quiz question generator focused on CONCEPTUAL UNDERSTANDING.

Your task is to create quiz questions that test theoretical knowledge, definitions, and fundamental principles.

Given a regulation chunk, you must:
1. Identify the key conceptual principle or definition
2. Create ONE multiple-choice question with EXACTLY 4 options
3. Mark which option is correct
4. Provide a short explanation (1 sentence) for EACH option explaining why it's correct or wrong

Output format (JSON):
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
  "focus": "conceptual"
}

Guidelines:
- Focus on "what is", "what does it mean", "how is it defined"
- Test understanding of principles, not application
- Ensure all wrong answers are plausible but clearly incorrect
- Keep explanations concise (one sentence each)
- Base everything strictly on the provided regulation text
"""

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """Initialize OpenAI client"""
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=api_base
        )
        self.model = "gpt-4o"
    
    def generate(self, chunk: Dict, improvement_feedback: Optional[str] = None) -> Dict:
        """Generate a conceptual question from a regulation chunk"""
        
        user_prompt = f"""Regulation Content:
Section: {chunk.get('title', 'Unknown')}
Number: {chunk.get('number', 'N/A')}
Type: {chunk.get('section_type', 'Unknown')}
Content: {chunk.get('content', '')}

Hierarchy: {' > '.join(chunk.get('hierarchy_path', []))}
"""
        
        if improvement_feedback:
            user_prompt += f"\n\nIMPROVEMENT FEEDBACK FROM HUMAN:\n{improvement_feedback}\n\nPlease incorporate this feedback."
        
        user_prompt += "\n\nGenerate ONE conceptual quiz question in JSON format."
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["generator"] = "conceptual"
        result["model"] = self.model
        
        return result