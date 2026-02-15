## Changelog

### Version 0.4.2 (2026-02-15)

Critical Bug Fixes:
- Fixed refiner not refining questions with warnings or issues
- Refiner now properly handles None values for warnings/issues fields
- Workflow now only stores refined questions if they were actually refined (checks for "refiner_model" field)
- Fixed logic to use explicit length checks instead of truthiness evaluation for warnings/issues lists
- Questions with warnings, issues, or score < 10 will now be properly refined

Code Quality Improvements:
- Added utility helpers module (parse_json_response, validate_qa_structure, build_chunk_context)
- Added comprehensive unit tests for utility helpers (30+ test cases)
- Improved test coverage for non-mocked utility functions

### Version 0.4.1 (2026-02-15)

Critical Bug Fixes:
- Fixed missing JSON parsing in all agents for Anthropic provider (was causing "local variable 'result' referenced before assignment" error)
- Fixed missing Cohere handling in practical_generator.generate() method (was causing "'function' object has no attribute 'completions'" error)
- Added JSON extraction logic for Anthropic responses in all 5 agents (conceptual_generator, practical_generator, validator, refiner, judge)
- All agents now properly handle markdown code blocks and parse JSON for both Anthropic and Cohere providers
- Fixed anthropic_api_base loading to support both ANTHROPIC_API_BASE and ANTHROPIC_BASE_URL environment variables
- Fixed cohere_api_key loading in __post_init__ method (was missing from environment variable loading)

### Version 0.4.0 (2026-02-14)

Cohere Provider Support:
- Added Cohere as a provider (replaces MiniMax)
- Uses Cohere's own SDK (`cohere.ClientV2`) with `COHERE_API_KEY` environment variable
- Cohere provider available for all agents (conceptual, practical, validator, refiner, judge)
- Updated examples to use Cohere instead of MiniMax
- Added `cohere_api_key` field to AgentConfig
- Updated documentation to reflect Cohere integration

Bug Fixes:
- Fixed Judge to accept individual valid questions instead of rejecting both when one fails
- Updated Judge prompt to handle 0, 1, or 2 questions (not assume pair)
- Fixed validation to skip None questions (previously validated conceptual even when None)
- Fixed max_tokens handling in all agents: now uses `self.max_tokens or 4096`
- Workflow now passes max_tokens only for Anthropic provider


### Version 0.3.8 (2026-02-14)

Refiner behavior and Judge architecture improvements:
- Fixed Judge agent to only return decision and reasoning (removed questions array from output)
- Updated workflow to construct final_questions based on Judge's decision, using refined questions from Refiner
- Refiner is now definitively the last agent to modify questions; Judge only makes accept/reject decisions
- Fixed all docstrings and comments in judge.py that incorrectly referenced refinement
- Updated agents.md documentation to clarify Judge output format (decision + reasoning only)

### Version 0.3.7 (2026-02-14)

Refiner agent separation:
- Refiner addresses validator warnings (suggestions) in addition to issues (critical problems) for better quality
- Refiner only skips refinement when: valid=true AND no warnings AND no issues AND score=10/10
- Updated workflow to follow: Generators -> Validator -> Refiner -> Judge -> Human
- Simplified Judge agent to only accept/reject (no longer does refinement)
- Added refiner_provider and refiner_model to AgentConfig
- Questions now come from: generators (if perfect) or refiner (if refined)

### Version 0.3.6 (2026-02-14)

Source reference automation and max_tokens fix:
- Removed `source_reference` field from all agent prompts (conceptual generator, practical generator, and judge) to prevent model hallucination
- Added automatic population of `source_reference` from chunk `hierarchy_path` in workflow for consistency and accuracy
- All questions now have reliable, traceable source references derived directly from document structure
- Add max_tokens required parameter for the Anthropic models

### Version 0.3.5 (2026-02-09)

Provider-default generation parameters:
- Removed temperature/max_tokens configuration from agents and config to rely on provider defaults.
- Updated agents to omit temperature/max_tokens parameters and refreshed docs/examples accordingly.


### Version 0.3.4 (2026-02-09)

Temperature/max_tokens behavior refinement:
- Removed global temperature/max_tokens defaults; per-agent values are optional and only sent when explicitly set.
- Updated generators/judge/validator to omit temperature/max_tokens unless provided.
- Refreshed agent documentation and examples to reflect per-agent settings.

### Version 0.3.3 (2026-02-08)

Per-agent temperature and token controls:
- Added per-agent temperature and max token settings with global defaults.
- Wired per-agent values into all generators, judge, and validator.
- Default temperature set to 1.0 for broader model compatibility.

### Version 0.3.2 (2026-02-08)

Code quality and example cleanup:
- Fixed lint issues across examples, CLI, agents, and parser (unused imports, f-string cleanup, ambiguous variable name).
- Adjusted example scripts to defer package imports until runtime and updated the multi-provider example.
- Normalized formatting with Black.

### Version 0.3.1 (2026-02-08)

Multi-provider and multi-model support:
- Added per-agent provider/model configuration (OpenAI, Anthropic, Google, Mistral) with provider-specific API key validation.
- Implemented provider-specific client paths in all agents and workflow wiring for flexible model selection.
- Added a multi-provider example script and updated dependencies for Google GenAI and Mistral SDKs.

### Version 0.3.0 (2026-02-08)

Test coverage and reliability improvements:
- Added comprehensive unit and integration tests for the EUR-Lex HTML parser, covering TOC extraction, chunking, and edge cases for EU regulations.
- Implemented robust CLI tests using subprocess to verify all command-line options, file outputs, error handling, and version reporting.
- Created agent tests for conceptual and practical question generators, including full mocking of OpenAI and Anthropic API calls, and validation of prompt logic and JSON extraction.
- Added validator agent tests to check strict structural/content requirements, batch validation, and error reporting.
- Added judge agent tests to cover all decision branches (accept, refine, reject) and ensure correct handling of validation results and model output.
- Ensured all tests pass in CI and locally, and set up automated coverage badge updates via GitHub Actions and Gist.

### Version 0.2.8 (2026-01-29)

Quiz generator prompt fix:
- Updated both conceptual and practical generator prompts to explicitly prohibit referencing any regulation, annex, article, section, or document name/number in the question text itself 
- All questions must be fully standalone and not misleading in multi-regulation scenarios

### Version 0.2.7 (2026-01-29)

Quiz output improvements:
- Remove duplicate print output
- Remove output print truncation

### Version 0.2.6 (2026-01-29)

Quiz workflow and output improvements:
- Validation scoring updated to be out of 10 (was previously out of 8)
- All output reporting now shows validation results before judge decision and reasoning, matching workflow logic
- All output questions now include generator/model metadata for traceability
- Updated all example scripts to print validation results before judge decision

### Version 0.2.5 (2026-01-29)

Quiz generation workflow refactor:
- Refactored workflow to validate both conceptual and practical Q&As before judging; judge now receives both Q&As and their validation results to make the final decision
- Updated validator prompt to clarify its role as a pre-screening step for the judge
- Updated judge prompt to require referencing validator results in decisions
- Fixed bug: judge now accepts validation_results as input and includes them in the model prompt
- Removed duplicate and dead code in workflow; ensured correct node order and argument passing
- Fixed syntax error in judge.py (unmatched parenthesis)

### Version 0.2.4 (2026-01-29)

Annex formatting fixes:
- Fixed line breaks after section/numbered headings (e.g., '1.', '2.') in annexes so numbers and text appear on the same line
- Ensured robust joining of list markers and their content for improved readability

### Version 0.2.3 (2026-01-28)

Annex content completeness:
- Fixed missing section and numbered headings (e.g., 1., 1.1., 1.2.) in annexes for full content fidelity
- Only the main annex title is removed; all other headings and structure are preserved
- Ensured all content, including section numbers and titles, is included in parsed output

### Version 0.2.2 (2026-01-28)

Annex parsing:
- Simplified annex content extraction using BeautifulSoup's get_text for robust, complete text output
- Improved formatting for list markers in annexes (e.g., (a), (i), —) to appear on the same line as their content
- Fixed and removed all AI/explanatory comments for a cleaner codebase
- Ensured no UnboundLocalError for re module in annex parsing

### Version 0.2.1 (2026-01-27)

Parallel workflow support:
- Introduced true parallel execution for conceptual and practical question generation
- Added a fan-out/fan-in node structure to safely merge parallel branches
- Updated human feedback loop to return to parallel start node instead of a single branch

### Version 0.2.0 (2026-01-27)

Initial LangGraph workflow setup:
- Defined the quiz generation workflow with sequential nodes: conceptual → practical → judge → validate → human feedback
- Added conditional branching based on human feedback (accept, reject, improve)
- Implemented node functions for conceptual/practical generation, judging, validation, and human feedback placeholder

### Version 0.1.11 (2026-01-26)

TOC cleanup:
- Removed 'Preamble content' as a separate TOC entry 
- Only 'Preamble' appears as the section header for a clean TOC


### Version 0.1.10 (2026-01-26)

Preamble extraction improvements:
- Added extraction of preamble text content before the first citation subdivision
- Ensured preamble content is chunked and included in the TOC for complete document coverage

### Version 0.1.9 (2026-01-20)

Annex section parsing enhancements:
- Added support for detecting and extracting annex sections (Section A, Section B, etc.) in addition to parts
- Fixed line break formatting in numbered lists within annex sections to keep numbers and content on same line
- Fixed content extraction for annex sections by searching for tables within container elements rather than direct table siblings
- Enhanced section pattern matching to support both "PART" and "Section" patterns with letter/number identifiers

### Version 0.1.8 (2026-01-19)

Complete text extraction:
- Simplified part content extraction to use natural text flow from HTML structure
- Fixed content duplication caused by nested table processing
- Fixed missing content (e.g., item (8)) by extracting all sibling elements between PART headers
- Switched from selective element processing to comprehensive text extraction using get_text()
- Ensures complete and accurate extraction without repetition for legal document compliance

### Version 0.1.7 (2026-01-19)

List structure preservation:
- Added detection and proper handling of list-item tables (numbered and lettered items)
- Fixed extraction of nested list structures by processing direct content only
- Preserved list markers like (8), (a), (b), (—) with their corresponding text
- Separated handling of list tables vs data tables for appropriate formatting

### Version 0.1.6 (2026-01-19)

Content extraction improvements:
- Enhanced part content extraction to include all paragraph types (titles, headings, body text)
- Fixed missing section titles and numbered headings in annex parts
- Lowered text length threshold to capture short titles (5 chars instead of 10)
- Added smart filtering to skip only PART headers while collecting all other content

### Version 0.1.5 (2026-01-19)

Bug fixes:
- Fixed annex TOC title to display with identifier (e.g., "ANNEX 1" instead of "ANNEX")
- Fixed empty content in annex parts by switching from sibling navigation to descendants iteration

### Version 0.1.4 (2026-01-19)

Annex parsing improvements:
- Added intelligent detection and parsing of parts within annexes (PART 1, PART 2, etc.)
- Improved part titles to include annex identifier (e.g., "ANNEX 1 - PART 1" instead of "ANNEX - PART 1")

Removed arbitrary content truncation in annexes and appendices - all content now preserved in full
Enhanced content collection for parts with proper boundary detection between sections

### Version 0.1.3 (2026-01-19)

Parser robustness improvements:
- Fixed parsing of articles directly under enacting terms (without chapter hierarchy)
- Enhanced article content extraction to handle table-based list items (e.g., (a), (b), (c) in table cells)
- Added proper appendix detection and parsing (distinguishes appendices from annexes)
- Improved title extraction for multi-paragraph appendix titles

### Version 0.1.2 (2026-01-18)

Text formatting and tooling:
- Implemented smart text cleaning for proper list formatting (removes extra newlines after list markers)
- Fixed numbered paragraph spacing
- Added professional command-line interface (CLI)
- Created comprehensive documentation with MkDocs and Material theme

### Version 0.1.1 (2026-01-18)

Parser enhancements:
- Added regulation title extraction and chunking
- Support for flexible 3-4 level hierarchy with sections within chapters
- Complete annexes extraction including table-based content
- Combined citations into single chunk matching EU-Lex structure
- Added concluding formulas parsing

### Version 0.1.0 (2026-01-17)

Initial release:
- EUR-Lex document parser
- Hierarchical document structure extraction
- Table of contents generation
- JSON export for chunks and TOC

