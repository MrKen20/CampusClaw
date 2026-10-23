## ADDED Requirements

### Requirement: Teacher app question-template editing
The system SHALL persist per-class question-template overrides and SHALL expose editing only on the teacher AI-app page.

#### Scenario: Save and synchronize
- **WHEN** a teacher saves a valid template with all declared placeholders
- **THEN** the class-local catalog and student preview show it after refresh or within5seconds while visible, and launch uses that latest template; role settings remain managed separately.

#### Scenario: Validation and isolation
- **WHEN** an update has unknown/missing placeholders, excessive rendered length or a stale version
- **THEN** it fails with400/409 without modification; students receive403 and one class cannot modify another class template.

### Requirement: Student conversation simplicity
The student conversation UI SHALL omit both trace-capture controls and trace-view buttons, including for existing traced messages.

#### Scenario: Saved trace exists
- **WHEN** the student opens a previously captured conversation
- **THEN** normal text, applicable citations and tool statuses remain, but no trace control appears; existing owner-only API diagnostics are not widened.

### Requirement: Applicable and actually-used references
The four applications SHALL exclude unrelated evidence before LLM calls, independently of the selected skill, and SHALL display only applicable citations actually used in the answer.

#### Scenario: Reading versus science
- **WHEN** reading/writing retrieves a science lecture, even with skills disabled or no route hit
- **THEN** that content never enters the application evidence and is not listed as a reference; old saved versions also hide those reference cards and invalid markers without rewriting stored audit data.

#### Scenario: Relevant evidence and unused candidates
- **WHEN** a correctly scoped material has sufficient content overlap and the answer cites its supplied index
- **THEN** that reference remains; unused candidates never appear as if referenced, and an unknown question subject yields no forced external reference.
