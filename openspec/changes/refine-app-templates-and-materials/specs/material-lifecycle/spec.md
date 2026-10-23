## ADDED Requirements

### Requirement: Edit class material
Teachers SHALL be able to edit a class material title/body with revision checks and server-side text validation.

#### Scenario: Valid edit
- **WHEN** the teacher saves the current version of a nonempty UTF-8 material
- **THEN** reading/download return the new text and title, old searchable chunks are invalidated, current content is reindexed, and a stale version receives409 without replacing data.

#### Scenario: Failed edit
- **WHEN** text/title are invalid or a file/database write fails
- **THEN** no partial new source becomes visible; original content remains; embedding failure after save retains the new source and clearly reports unavailable indexing.

### Requirement: Delete class material
Teachers SHALL have a trash action with a second confirmation before deleting a material and its active knowledge/bindings.

#### Scenario: Confirmed deletion
- **WHEN** deletion of the current version succeeds
- **THEN** list/detail/download exclude it, knowledge entries/chunks and agent bindings are gone, vector/file cleanup is attempted, search cannot return its stale points, and restart does not recreate a renamed/deleted seed.

#### Scenario: Cancel and authorization
- **WHEN** confirmation is canceled
- **THEN** no DELETE is sent; students receive403 on writes and cross-class requests return the same404 as nonexistent materials.

#### Scenario: Concurrent indexing
- **WHEN** an old index/reindex task overlaps edit or delete
- **THEN** per-material serialization and a fresh database read prevent stale text or deleted-material chunks from being reintroduced.
