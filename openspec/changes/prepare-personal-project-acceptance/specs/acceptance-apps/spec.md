## ADDED Requirements

### Requirement: Built-in AI task applications and prompt templates
The platform SHALL provide four functional applications (concept explanation, reading analysis, writing coaching, mistake review), each with its own task input and system/user prompt templates, a class-local agent and a built-in skill.

#### Scenario: Student launches an application
- **WHEN** a student submits valid application fields
- **THEN** the server creates a private conversation with the enabled class-local app agent and returns a rendered editable question of at most500 characters; sending it uses real streaming, knowledge retrieval and the existing tool runtime.

#### Scenario: Teacher configures a template
- **WHEN** the teacher selects an application role template in the agent editor
- **THEN** it populates only the draft; saving persists the role prompt and existing bindings remain configurable.

#### Scenario: Deleted or disabled application
- **WHEN** the app agent has been deleted or disabled
- **THEN** launch fails without creating a conversation and restart never overwrites teacher edits or resurrects the deleted agent.

#### Scenario: App-specific evidence boundaries
- **WHEN** reading/writing or mistake review retrieves materials with unrelated subject titles
- **THEN** the built-in skill excludes those materials from model evidence; writing examples are marked hypothetical instead of asserted to be the student's experience; default upgrades only affect unchanged built-in source.

### Requirement: SKILL.md import with bounded resources
The platform SHALL accept a standard SKILL.md file or a ZIP containing exactly one SKILL.md and bounded text resources, while preserving legacy skill files and Go-side upload validation.

#### Scenario: Valid skill package
- **WHEN** the teacher uploads a package with valid name/description metadata and instruction body
- **THEN** the skill and its text resources persist in the teacher's class and can be bound using existing controls; only the selected enabled skill's instruction body enters the LLM context, not all skills or all resources.

#### Scenario: Unsafe package
- **WHEN** an archive omits SKILL.md, contains traversal/absolute paths, links, duplicates, unsupported/binary files or exceeds limits
- **THEN** the server rejects it with400 without writing partial data; students receive403 and other classes cannot access it.

### Requirement: Per-turn LLM request evidence
The platform SHALL provide opt-in, owner-only details of actual LLM request bodies and raw responses, including native tool planning and final SSE, with explicit truncation limits and no authorization headers or environment credentials.

#### Scenario: Trace enabled
- **WHEN** the owner sends a message with capture_trace=true
- **THEN** the saved assistant message links to isolated per-request entries containing exact model/messages/parameters, raw JSON or SSE response, HTTP status and truncation status, viewable after refresh.

#### Scenario: Trace disabled or access denied
- **WHEN** capture is not requested, or a teacher/another student/another class requests a private trace
- **THEN** capture is not stored by default; unauthorized role is403 and a nonowner receives the same404 as a missing trace.

#### Scenario: Truthful evidence interpretation
- **WHEN** explaining the model inputs
- **THEN** the platform distinguishes rendered templates, bounded retrieved chunks, only the activated skill body, bounded history, candidate tool definitions and actual tool result messages; it never equates full skill library loading with loading the selected instruction body.
