# Multi-Agent Quiz Generation System

## Overview

The quiz generation system uses a multi-agent architecture powered by LangGraph to create high-quality quiz questions from regulatory documents. The system employs four specialized AI agents that work together to generate, judge, and validate questions, with configurable providers and models per agent.

## Architecture

### Agent Roles

The system consists of four agents, each with a specific responsibility:

1. **Conceptual Generator**: Generates questions focused on theoretical understanding, definitions, and fundamental principles
2. **Practical Generator**: Creates scenario-based questions testing real-world application of regulations
3. **Validator**: Performs strict validation to ensure questions meet structural and content requirements
4. **Judge**: Receives both Q&As and their validation results, and makes the final decision on which questions (0, 1, or 2) to accept or refine for the end user

Supported providers (alphabetical): **Anthropic**, **Google**, **Mistral**, **OpenAI**. Any text-generation model from these providers can be used by passing the model name directly.

### Workflow Pipeline

```
┌─────────────────────┐
│ Input: Regulation   │
│ Chunk (Article)     │
└──────────┬──────────┘
           │
           v
┌──────────────────────────────────┐
│  Parallel Generation             │
├──────────────────────────────────┤
│  ┌────────────────┐              │
│  │ Conceptual Gen │              │
│  └────────┬───────┘              │
│           │                      │
│           v                      │
│  ┌────────────────┐              │
│  │ Practical Gen  │              │
│  └────────┬───────┘              │
└───────────┼──────────────────────┘
            │
            v
┌───────────────────────┐
│  Validator            │
│  - Format Check       │
│  - Content Check      │
│  - Quality Score      │
└──────────┬────────────┘
           │
           v
┌───────────────────────┐
│  Judge                │
│  - Accept Both        │
│  - Accept One         │
│  - Unify              │
│  - Reject Both        │
└──────────┬────────────┘
           │
           v
┌───────────────────────┐
│  Human Feedback       │
│  - Accept             │
│  - Reject             │
│  - Request Improve    │
└───────────────────────┘
```

## Agent Details

### Conceptual Generator

**Purpose**: Generate questions that test theoretical knowledge and understanding of regulatory concepts.

**Model**: Configurable provider/model

**Focus Areas**:
- Definitions and terminology
- Fundamental principles
- Theoretical frameworks
- "What is" and "how is it defined" questions

**Output Format**:
```json
{
  "question": "Question text",
  "options": {
    "A": "First option",
    "B": "Second option",
    "C": "Third option",
    "D": "Fourth option"
  },
  "correct_answer": "A",
  "explanations": {
    "A": "Why this is correct",
    "B": "Why this is wrong",
    "C": "Why this is wrong",
    "D": "Why this is wrong"
  },
  "source_reference": "Article X, Chapter Y",
  "difficulty": "easy|medium|hard",
  "focus": "conceptual"
}
```

### Practical Generator

**Purpose**: Create scenario-based questions that test application of regulations in real-world situations.

**Model**: Configurable provider/model

**Focus Areas**:
- Real-world scenarios
- Application of rules
- Decision-making situations
- "What should you do" and "how would you apply" questions

**Output Format**: Same JSON structure as Conceptual Generator, with `"focus": "practical"`

### Judge

**Purpose**: Evaluate both generated questions and decide on the best output strategy.

**Model**: Configurable provider/model

**Decision Types**:

1. **accept_both**: Both questions are high quality and test different aspects
2. **accept_conceptual**: Only the conceptual question is valid and high quality
3. **accept_practical**: Only the practical question is valid and high quality
4. **refine_conceptual**: Conceptual question needs refinements
5. **refine_practical**: Practical question needs refinements
6. **refine_both**: Both questions need refinements
7. **reject_both**: Neither question is suitable

**Evaluation Criteria**:
- Validator's pass/fail and issues for each question (primary filter)
- Accuracy: Does it correctly reflect the regulation?
- Clarity: Is the question unambiguous?
- Quality: Are all options plausible? Are explanations clear?
- Distinctiveness: Do the two questions test different skills?
- Difficulty: Is it appropriate for certification level?

**Output Format**:
```json
{
  "decision": "accept_both|accept_conceptual|accept_practical|reject_both|refine_conceptual|refine_practical|refine_both",
  "reasoning": "Brief explanation of your decision, referencing validator results",
  "improvements_made": ["List of improvements if refined"],
  "questions": [
    {
      "question": "The question text",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct_answer": "A",
      "explanations": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "source_reference": "Article X, Chapter Y",
      "difficulty": "easy|medium|hard",
      "focus": "conceptual|practical"
    }
  ]
}
```

### Validator

**Purpose**: Perform strict validation of question format and content requirements before judging.


**Model**: Configurable provider/model

**Validation Checks (run before judging):**

**Structural Requirements**:
1. Has exactly 4 multiple choice options (A, B, C, D)
2. Has exactly one correct answer marked
3. Has explanation for all 4 options
4. Each explanation is 1-2 sentences maximum
5. Question text is clear and complete

**Content Requirements**:
6. Correct answer explanation confirms why it's right
7. Wrong answer explanations explain why they're wrong (act as hints)
8. All options are plausible (not obviously wrong)
9. Question is unambiguous
10. Based strictly on provided regulation content

**Output Format**:
```json
{
  "valid": true,
  "issues": [],
  "warnings": [],
    "checks_passed": {
      "has_4_options": true,
      "has_correct_answer": true,
      "has_all_explanations": true,
      "explanations_concise": true,
      "question_clear": true,
      "correct_explanation": true,
      "wrong_explanations_are_hints": true,
      "options_plausible": true,
      "question_unambiguous": true,
      "regulation_based": true
    },
  "score": 10
}
```

## State Management

The workflow uses LangGraph's state management to track progress through the pipeline.

### State Schema

```python
{
  # Input
  "chunk": Dict,                    # Regulation chunk to process
  "improvement_feedback": str,      # Optional human feedback
  
  # Generated Q&As
  "conceptual_qa": Dict,           # Output from conceptual generator
  "practical_qa": Dict,            # Output from practical generator
  

  # Validation results (before judging)
  "validation_results": List[Dict], # Results for each question
  "all_valid": bool,               # Whether all passed validation

  # Judge output
  "judge_decision": str,           # accept_both|accept_conceptual|accept_practical|reject_both|unify
  "judge_reasoning": str,          # Explanation (references validator results)
  "judged_qas": Dict,              # Final Q&As after judging
  
  # Final output
  "final_questions": List[Dict],   # Questions ready for use
  
  # Human feedback
  "human_feedback": str,           # Improvement suggestions
  "human_action": str,             # accept|reject|improve
  
  # Status
  "current_step": str,             # Current workflow step
  "errors": List[str]              # Any errors encountered
}
```

## Configuration

### Agent Configuration

All agents are configured through the `AgentConfig` class:

```python
from quiz_gen.agents.config import AgentConfig

config = AgentConfig(
  # API Keys (or load from environment)
  openai_api_key="sk-...",
  anthropic_api_key="sk-ant-...",
  google_api_key="...",  # or GEMINI_API_KEY via .env
  mistral_api_key="...",

  # Provider + Model Selection per agent
  conceptual_provider="openai",
  practical_provider="anthropic",
  validator_provider="google",
  judge_provider="mistral",
  conceptual_model="gpt-4o",
  practical_model="claude-sonnet-4-20250514",
  validator_model="gemini-2.5-flash",
  judge_model="mistral-large-latest",

  # Per-agent Generation Settings
  conceptual_temperature=1.0,
  practical_temperature=1.0,
  judge_temperature=1.0,
  validator_temperature=1.0,
  conceptual_max_tokens=2000,
  practical_max_tokens=2000,
  judge_max_tokens=3000,
  validator_max_tokens=2000,

  # Workflow Settings
  auto_accept_valid=False,
  save_intermediate_results=True,
  output_directory="data/quizzes",

  # Validation Settings
  min_validation_score=6,
  strict_validation=True,
)
```

### Environment Variables

The system automatically loads configuration from a `.env` file:

```bash
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
MISTRAL_API_KEY=your_mistral_key
GOOGLE_API_KEY=your_google_key
# GEMINI_API_KEY is also supported as an alias for Google
```

## Usage

### Basic Usage

```python
from quiz_gen.agents.workflow import QuizGenerationWorkflow
from quiz_gen.agents.config import AgentConfig

# Initialize
config = AgentConfig()
workflow = QuizGenerationWorkflow(config)

# Process a single chunk
chunk = {
    "section_type": "article",
    "number": "47",
    "title": "Article 47 - Delegated powers",
    "content": "...",
    "hierarchy_path": ["Article 47"]
}

result = workflow.run(chunk)
```

### Batch Processing

```python
# Process multiple chunks
chunks = load_chunks_from_file("data/processed/regulation.json")
results = workflow.run_batch(chunks, save_output=True)
```

### With Improvement Feedback

```python
# First attempt
result = workflow.run(chunk)

# If human requests improvements
result = workflow.run(
    chunk, 
    improvement_feedback="Make the question more specific to drones"
)
```

## Human-in-the-Loop

The workflow includes a placeholder for human feedback integration. In production, this connects to a UI where domain experts can:

1. **Review generated questions**: See both conceptual and practical questions with all options and explanations
2. **Accept questions**: Approve high-quality questions for the quiz database
3. **Reject questions**: Discard questions that don't meet standards
4. **Request improvements**: Provide specific feedback that will be incorporated in the next generation cycle

### Human Feedback Loop

When human feedback is "improve", the workflow:
1. Captures the improvement suggestions
2. Routes back to the generation stage
3. Passes feedback to both generators
4. Generators incorporate the feedback into their prompts
5. New questions are generated, judged, and validated
6. Process repeats until accepted or rejected

## Output

### Question Output Format

Each validated question includes:

```json
{
  "question": "Full question text with scenario if practical",
  "options": {
    "A": "Option A text",
    "B": "Option B text",
    "C": "Option C text",
    "D": "Option D text"
  },
  "correct_answer": "A",
  "explanations": {
    "A": "Explanation of why A is correct",
    "B": "Hint about why B is wrong",
    "C": "Hint about why C is wrong",
    "D": "Hint about why D is wrong"
  },
  "source_reference": "Article 47, Section 1(a)",
  "difficulty": "medium",
  "focus": "conceptual",
  "generator": "conceptual",
  "model": "gpt-4o"
}
```

### Saved Results

Results are saved to JSON files in the configured output directory:

```json
{
  "chunk": {...},
  "questions": [...],
  "judge_decision": "accept_both",
  "judge_reasoning": "...",
  "validation_results": [...],
  "all_valid": true,
  "errors": []
}
```

## Error Handling

The workflow includes comprehensive error handling:

- **Generation failures**: Captured and logged, workflow continues
- **API errors**: Retry logic with configurable attempts
- **Validation failures**: Questions are not saved, errors are reported
- **State errors**: Tracked in the errors list for debugging

Errors are accumulated in the state and can be reviewed in the final output.

## Performance Considerations

### API Calls per Chunk

For each regulation chunk:
- 2 parallel generation calls (OpenAI + Claude)
- 1 judge call (Claude)
- 1-2 validation calls (OpenAI, depends on judge decision)

**Total: 4-5 API calls per chunk**

### Cost Optimization

- Use parallel generation to minimize latency
- Judge reduces redundant questions
- Validator prevents low-quality questions from requiring regeneration
- Batch processing amortizes initialization overhead

### Caching

The workflow uses LangGraph's `MemorySaver` checkpoint to enable:
- Resume interrupted workflows
- Review historical decisions
- Debug state transitions

## Extension Points

The system is designed to be extensible:

1. **Add new agent types**: Implement new generators with different focuses
2. **Custom validation rules**: Extend the Validator with domain-specific checks
3. **Alternative models**: Configure different LLMs for each role
4. **Custom workflows**: Modify the LangGraph pipeline for different processes
5. **Storage backends**: Implement custom storage for questions (database, cloud)

## Best Practices

1. **Review judge decisions**: Monitor acceptance rates to tune generator prompts
2. **Track validation scores**: Identify common failure patterns
3. **Analyze question diversity**: Ensure conceptual and practical questions are distinct
4. **Collect human feedback**: Use feedback to improve generator prompts over time
5. **Version control prompts**: Track prompt changes and their impact on quality
6. **Monitor API costs**: Set budgets and rate limits appropriately
7. **Test with sample data**: Validate workflow before processing large batches

## Troubleshooting

### Common Issues

**Questions are too similar**:
- Review generator prompts for overlap
- Adjust temperature settings
- Provide more specific focus instructions

**Low validation scores**:
- Check explanation quality
- Ensure options are distinct
- Verify questions are based on source content

**Judge always unifies**:
- Questions may be too similar
- Consider adding more diversity to generator prompts
- Review sample outputs from both generators

**High API costs**:
- Enable caching where possible
- Process in smaller batches
- Use lower-cost models for validation if appropriate

## See Also

- [Parsers Documentation](parsers.md) - How to parse regulation documents
