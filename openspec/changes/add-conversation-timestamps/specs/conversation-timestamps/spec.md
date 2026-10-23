## ADDED Requirements

### Requirement: Relative conversation activity
The student conversation index SHALL show a relative last-activity time alongside each agent name and SHALL retain most-recent-activity ordering.

#### Scenario: Historical and active conversations
- **WHEN** the student views conversations or sends a new message
- **THEN** each index displays 刚刚 or elapsed minutes/hours/days/months/years, based on the latest saved message or conversation activity; empty conversations fall back to creation time; visible labels refresh within a minute and on refocus.

### Requirement: Authoritative message times
User and assistant messages SHALL expose stable server timestamps and display them as 北京时间 YYYY年MM月DD日HH:mm.

#### Scenario: History and streaming agree
- **WHEN** a response streams and is later reopened, including a saved interrupted response
- **THEN** message times match the original server values, user time means accepted-message creation and assistant time means response generation start; the browser does not fabricate a saved timestamp while acceptance is pending.

#### Scenario: Timezone and invalid dates
- **WHEN** the browser uses another timezone or encounters an absent/invalid timestamp
- **THEN** valid times still display in Asia/Shanghai with an absolute-time tooltip; invalid dates never display Invalid Date or a fabricated 刚刚.

### Requirement: Time metadata boundary
Time metadata SHALL be additive to existing conversation/history/SSE APIs and SHALL NOT change LLM request construction or access control.

#### Scenario: Unchanged model inputs and privacy
- **WHEN** timestamps are returned in history and stream metadata
- **THEN** model messages still contain only the existing role/content/tool fields, timestamps are absent from LLM payloads, and other students/classes cannot read the conversation.
