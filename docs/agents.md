# Multi-Agent Quiz Generation System

## Overview

The quiz generation system uses a multi-agent architecture powered by LangGraph to create high-quality quiz questions from regulatory documents. The system employs four specialized AI agents that work together to generate, judge, and validate questions, with configurable providers and models per agent.

## Architecture

### Agent Roles

The system consists of five agents, each with a specific responsibility:

1. **Conceptual Generator**: Generates questions focused on theoretical understanding, definitions, and fundamental principles
2. **Practical Generator**: Creates scenario-based questions testing real-world application of regulations
3. **Validator**: Performs strict validation to ensure questions meet structural and content requirements
4. **Refiner**: Fixes issues identified by the validator while preserving the original question's intent
5. **Judge**: Makes the final decision on which questions to accept or reject for the end user

Supported providers: **Anthropic**, **Google**, **Mistral**, **OpenAI**, and **Cohere**.

### Workflow Pipeline

```
┌─────────────────────┐
│ Input: Regulation   │
│ Chunk (Article)     │
└──────────┬──────────┘
           │
           v
    ┌──────┴──────┐
    │             │
    v             v
┌────────────┐ ┌────────────┐
│Conceptual  │ │Practical   │  (Parallel)
│Generator   │ │Generator   │
└─────┬──────┘ └──────┬─────┘
      │               │
      └───────┬───────┘
              │
              v
┌───────────────────────┐
│  Validator            │
│  - Format Check       │
│  - Content Check      │
│  - Quality Score      │
│  (Both Q&As)          │
└──────────┬────────────┘
           │
           v
┌───────────────────────┐
│  Refiner              │
│  - Issues + Warnings  │
│  - Preserve Intent    │
└──────────┬────────────┘
           │
           v
┌───────────────────────┐
│  Judge                │
│  - Accept Both        │
│  - Accept One         │
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

### Question Generators (Conceptual & Practical)

**Models**: Configurable provider/model per generator

**Conceptual Generator** focuses on theoretical knowledge:
- Definitions and terminology
- Fundamental principles
- "What is" and "how is it defined" questions

**Practical Generator** focuses on real-world application:
- Scenario-based questions
- Application of rules
- "What should you do" and "how would you apply" questions

**Important Constraint**: Questions must NOT reference regulation names, numbers, articles, or sections. Questions must be fully standalone to prevent confusion in multi-regulation scenarios.

**Output Format**:
```json
{
  "question": "Question text",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "correct_answer": "A",
  "explanations": {"A": "Why correct", "B": "Why wrong", "C": "Why wrong", "D": "Why wrong"},
  "difficulty": "easy|medium|hard",
  "focus": "conceptual|practical"
}
```

### Refiner

**Purpose**: Fix issues identified by the validator while preserving the original question's intent and focus.

**Model**: Configurable provider/model

**Refinement Actions**:
- Fix options that are not plausible enough
- Improve explanations that don't properly hint at why wrong answers are incorrect
- Clarify unclear or ambiguous question wording
- Complete missing or incomplete explanations
- Adjust options that are too obviously wrong

**Important**: The refiner only runs on questions that failed validation. Questions that pass validation are returned unchanged.

**Output Format**: Same JSON structure as generators, with additional field:
```json
{
  ...
  "refinement_notes": "Brief description of what was fixed",
  "refiner_model": "gpt-4o"
}
```

### Validator

**Purpose**: Perform strict validation of question format and content requirements before refinement.


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

### Judge

**Purpose**: Make the final accept/reject decision on refined questions.

**Model**: Configurable provider/model

**Decision Types**:

1. **accept_both**: Both questions are high quality and test different aspects
2. **accept_conceptual**: Only the conceptual question is acceptable
3. **accept_practical**: Only the practical question is acceptable
4. **reject_both**: Neither question meets the required standards

**Important**: The judge does NOT refine questions. Questions are already refined by the Refiner agent before reaching the judge. The judge only decides which refined questions to accept.

**Evaluation Criteria**:
- Validator's pass/fail and issues for each question (primary filter)
- Whether refinement successfully addressed the issues
- Accuracy: Does it correctly reflect the regulation?
- Distinctiveness: Do the two questions test different skills?
- Difficulty: Is it appropriate for certification level?

**Output Format**:
```json
{
  "decision": "accept_both|accept_conceptual|accept_practical|reject_both",
  "reasoning": "Brief explanation of your decision, referencing validator results"
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
  
  # Validation results (before refinement)
  "validation_results": List[Dict], # Results for each question
  "all_valid": bool,               # Whether all passed validation

  # Refined Q&As (after refinement)
  "refined_conceptual_qa": Dict,   # Refined conceptual question
  "refined_practical_qa": Dict,    # Refined practical question

  # Judge output
  "judge_decision": str,           # accept_both|accept_conceptual|accept_practical|reject_both
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

  # Provider + Model Selection per agent
  conceptual_provider="openai",
  practical_provider="anthropic",
  validator_provider="google",
  refiner_provider="openai",
  judge_provider="mistral",
  conceptual_model="gpt-4o",
  practical_model="claude-sonnet-4-20250514",
  validator_model="gemini-2.5-flash",
  refiner_model="gpt-4o",
  judge_model="mistral-large-latest",

  # Provider-Specific Settings
  anthropic_max_tokens=4096,  # Required by Anthropic API (default: 4096)

  # Workflow Settings
  auto_accept_valid=False,
  save_intermediate_results=True,
  output_directory="data/quizzes",

  # Validation Settings
  min_validation_score=6,
  strict_validation=True,
)

# Note: Temperature is not configured and provider defaults are used.
```

#### Using Cohere

Cohere uses its own SDK:

```python
config = AgentConfig(
  # Use Cohere for some agents (uses COHERE_API_KEY)
  conceptual_provider="cohere",
  conceptual_model="command-r-plus-08-2024",  # Cohere model name
  
  # Can still use other providers
  validator_provider="openai",
  judge_provider="anthropic",  # Regular Anthropic/Claude
)
```

### Environment Variables

The system automatically loads configuration from a `.env` file:

```bash
# Anthropic - Used for Claude models
ANTHROPIC_API_KEY=your_anthropic_key

OPENAI_API_KEY=your_openai_key
MISTRAL_API_KEY=your_mistral_key
GOOGLE_API_KEY=your_google_key
COHERE_API_KEY=your_cohere_key
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
  "source_reference": "Regulation X > Section Y > Article Z",
  "difficulty": "medium",
  "focus": "conceptual",
  "generator": "conceptual",
  "model": "gpt-4o"
}
```

**Note**: The `source_reference` field is added by the workflow (not by agents) from the chunk's `hierarchy_path`, formatted as elements joined with " > ".

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

- **Generation failures**: Captured and logged in the errors list, workflow continues
- **Validation failures**: Questions that fail validation are not accepted
- **State errors**: Tracked in the errors list for debugging

Errors are accumulated in the state and can be reviewed in the final output.

Note: Retry logic for API errors is configured in AgentConfig but not currently implemented in the workflow.

## Performance Considerations

### API Calls per Chunk

For each regulation chunk:
- 2 parallel generation calls (conceptual + practical)
- 2 validation calls (one for each generated question)
- 2 refinement calls (one for each question, skipped if validation passes)
- 1 judge call

**Total: Up to 7 API calls per chunk** (5 if both questions pass validation)

### Cost Optimization

- Use parallel generation to minimize latency
- Validator prevents low-quality questions from requiring regeneration
- Judge reduces redundant questions
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

1. **Analyze question diversity**: Ensure conceptual and practical questions are distinct
2. **Track validation scores**: Identify common failure patterns
3. **Review judge decisions**: Monitor acceptance rates to tune generator prompts
4. **Collect human feedback**: Use feedback to improve generator prompts over time
5. **Version control prompts**: Track prompt changes and their impact on quality
6. **Monitor API costs**: Set budgets and rate limits appropriately
7. **Test with sample data**: Validate workflow before processing large batches

## See Also

- [Parsers Documentation](parsers.md) - How to parse regulation documents
