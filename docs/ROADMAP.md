# Vibeguard — Roadmap

## Phase 1: Foundation (Weeks 1-2)

**Goal:** Working SDK that can capture and log actions.

### Deliverables

- [ ] Project setup (monorepo, TypeScript, tests)
- [ ] `@vibeguard/core` — Action logging engine
  - [ ] Action data model
  - [ ] SQLite storage
  - [ ] Risk classification
  - [ ] Query APIs
- [ ] `@vibeguard/sdk` — Agent integration library
  - [ ] Action capture
  - [ ] Basic gating (terminal prompt)
  - [ ] TypeScript types
- [ ] CLI tool
  - [ ] `vibeguard log` — view recent actions
  - [ ] `vibeguard tail` — live stream
  - [ ] `vibeguard undo <id>` — rollback
- [ ] Basic docs and README

### Success Criteria

- Can integrate with any Node.js agent
- Actions logged to SQLite
- Risk levels assigned automatically
- Can view logs via CLI

---

## Phase 2: User Experience (Weeks 3-4)

**Goal:** Dashboard and undo system.

### Deliverables

- [ ] `@vibeguard/dashboard` — Web UI
  - [ ] Timeline view
  - [ ] Action details
  - [ ] Filter/search
  - [ ] Settings page
- [ ] Undo system
  - [ ] Undo registry
  - [ ] File backup/restore
  - [ ] Config rollback
- [ ] Clawdbot integration
  - [ ] Plugin/skill for Clawdbot
  - [ ] Auto-capture all tool calls
- [ ] Notifications
  - [ ] Desktop notifications
  - [ ] Terminal alerts

### Success Criteria

- Users can see what their agent did in a web UI
- Can undo file operations
- Clawdbot users can install with one command

---

## Phase 3: Intent & Control (Weeks 5-6)

**Goal:** Smart gating and policy rules.

### Deliverables

- [ ] Enhanced intent gating
  - [ ] Rich approval UI
  - [ ] Context display
  - [ ] "Always allow" / "Always block" options
- [ ] Policy rules engine
  - [ ] YAML configuration
  - [ ] Condition matching
  - [ ] Custom rules
- [ ] Plain English explanations
  - [ ] LLM-powered summaries
  - [ ] Context-aware descriptions
- [ ] Session grouping
  - [ ] Conversation boundaries
  - [ ] Session summaries

### Success Criteria

- Users can define custom policies
- Actions explained in plain English
- Related actions grouped together

---

## Phase 4: Scale & Enterprise (Weeks 7-8)

**Goal:** Team features and compliance.

### Deliverables

- [ ] Multi-agent support
  - [ ] Agent registry
  - [ ] Per-agent policies
  - [ ] Aggregate views
- [ ] Team sharing
  - [ ] PostgreSQL backend option
  - [ ] User management
  - [ ] Role-based access
- [ ] Compliance exports
  - [ ] PDF audit reports
  - [ ] CSV exports
  - [ ] SIEM integration
- [ ] API server
  - [ ] REST API for external tools
  - [ ] Webhooks for events

### Success Criteria

- Teams can share a Vibeguard instance
- Exportable audit reports
- Integration with enterprise tools

---

## Future Ideas (Backlog)

- [ ] Mobile app for approvals
- [ ] Voice notifications
- [ ] AI-powered anomaly detection
- [ ] Cross-device sync
- [ ] Browser extension for web agents
- [ ] Marketplace for policy templates
- [ ] Integration with more agents (GPT Operator, etc.)

---

## Non-Goals (What We're NOT Building)

- Full observability platform (LangSmith does this)
- LLM debugging tools (Arize does this)
- Agent framework (LangChain does this)
- Security scanner (other tools do this)

**We focus on:** User-facing audit + intent verification.

---

*Last updated: 2026-01-29*
