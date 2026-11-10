---
name: outbound-replies
description: Draft grounded replies for an existing outbound campaign from supplied or authorized mailbox evidence.
metadata:
  category: managed
---

# Outbound Replies

Adapted from the MIT-licensed [Graphed outbound plugin](https://github.com/graphed-inc/marketing-skills/tree/main/plugins/outbound). The original Instantly sync, Postgres tables, dashboard, scheduler, and Graphed OpenRouter proxy are not part of this package.

Require a campaign playbook, sender identity, audience, tone, approved claims, a real inbound thread or synthetic test message, and a durable task output location. Apollo can provide campaign, sequence, contact, enrollment, and suppression context when its tools are granted. Gmail can provide the actual mailbox thread and reply draft when that mailbox is granted. Inspect both tool catalogs and match the sender, recipient, campaign, and thread identities before combining evidence. Apollo's synchronized reply state may lag the mailbox; read the current Gmail thread before finalizing a reply. If neither an authorized connector nor supplied thread evidence exists, return `needs_input`. Never request a separate model key: use the deployed Stimulir model gateway.

Default mode is **draft**. Read the full relevant thread, campaign playbook, opt-out and reply state, then produce a reply that answers the latest message. Keep unsupported product claims out. Respect opt-outs, bounces, existing human replies, and campaign suppression rules. Save the draft and source/thread IDs in a durable artifact; do not send, enqueue, or schedule it implicitly. Use the harness browser or configured browser-use path only for contextual website research, not as a substitute for a granted mailbox or Apollo tool. A synthetic test must never call a live send tool.

Sending requires an explicit user request, a final reviewable recipient, subject, and body, a granted send tool, and a fresh check of thread and suppression state immediately before dispatch. Select one sending system, Apollo or Gmail, for that reply; do not dispatch through both. Use an idempotency key or provider message ID to prevent duplicate sends. A connector failure or uncertain send must remain `pending_reconciliation`; do not retry blindly. Recurring sync or auto-send needs its own explicit approval and a durable job implementation outside this skill.

Return `drafted`, `sent`, `needs_input`, or `blocked` with source and provider IDs. Do not claim a draft reached a mailbox. No Graphed CLI, `INSTANTLY_API_KEY`, or Graphed project is assumed.
