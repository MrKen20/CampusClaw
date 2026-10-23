## Context

Conversation rows already have created_at/updated_at; message rows have created_at but Message JSON omits it. updated_at currently advances only on user messages. Tutor creates optimistic placeholders and reloads persisted messages after streaming.

## Goals / Non-Goals

Provide stable server time through streaming and history with no database migration or new dependency. Preserve all existing model behavior and prior uncommitted work; see proposal Non-goals.

## Decisions

1. Query MySQL TIMESTAMP values via UNIX_TIMESTAMP and format RFC3339 UTC in Go. This avoids treating a server-local SQL date as browser-local time. Effective conversation updated_at is the greatest of its stored activity and latest saved message creation time, so old assistant replies also participate without rewriting history.
2. Add Message.created_at. First SSE meta includes user_created_at from its saved row and assistant_created_at from the server's generation-start clock; save the assistant using that same Unix instant via FROM_UNIXTIME. Stop/failure persistence uses the same instant. No client timestamp is accepted. Existing clients can ignore additive metadata.
3. Frontend placeholders show pending labels until authoritative metadata arrives; reconcile user and assistant times, update local sidebar activity and sort, then accept history/list values after completion. A 30-second display clock plus focus/visibility events updates relative labels without polling model endpoints. Format all absolute labels and tooltips in Asia/Shanghai, with semantic time elements.
4. Document current model/Skill behavior from source and existing trace evidence. In particular, distinguish the activated skill's instruction body from complete SKILL.md/package; do not claim that skill instructions are absent merely because the raw package is not sent.

## Risks / Trade-offs

- SQL latest-message lookup adds per-conversation index work → existing conversation_id index bounds the lookup; no global scan or migration.
- Future/invalid client dates → clamp future elapsed time to zero, omit invalid message timestamps and use 时间未知 for invalid index times.
- Streaming may fail before first meta → keep pending indicator until history reload supplies the saved user timestamp; never invent a persisted time.

## Migration Plan

Rebuild api/web together; additive JSON fields allow previous clients. No historical row changes. Rollback consists of deploying previous images.
