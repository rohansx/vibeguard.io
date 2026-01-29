# Vibeguard — Project Plan

## Vision

**Vibeguard** is an open-source intent verification and audit system for AI agents. It answers two questions:

1. **What did my AI agent do?** (Audit)
2. **Did I actually want it to do that?** (Intent)

## Problem Statement

AI agents like Clawdbot, Claude Code, and GPT Operator are getting root access to people's lives — sending emails, deleting files, posting tweets, making purchases. The only safeguard is "are you sure? y/n".

**Current landscape:**
- **Observability tools (LangSmith, Arize)** — Dev-focused, not user-facing
- **Identity verification (Prove, HUMAN)** — Agent identity, not human intent
- **Nothing exists** for end-users to see/control what their agents do

## Core Principles

1. **User-first** — Built for humans, not just developers
2. **Agent-agnostic** — Works with any AI agent
3. **Open-source** — Transparency is non-negotiable for trust
4. **Privacy-preserving** — Logs stay local by default
5. **Simple** — Ship fast, iterate often

## Target Users

1. **End-users** running AI agents (Clawdbot, etc.)
2. **Developers** building AI agents who need audit trails
3. **Enterprises** needing compliance/governance

## Competitive Positioning

| Feature | LangSmith | Arize | Vibeguard |
|---------|-----------|-------|-----------|
| Audience | Developers | ML teams | End-users + Devs |
| Focus | Debugging | Monitoring | Audit + Intent |
| User-facing UI | ❌ | ❌ | ✅ |
| Action classification | ❌ | ❌ | ✅ |
| Undo/rollback | ❌ | ❌ | ✅ |
| Open-source | Partial | ❌ | ✅ |

## Success Metrics

- **Phase 1:** 100 GitHub stars, 10 active users
- **Phase 2:** 1,000 stars, integration with 3+ agents
- **Phase 3:** 10,000 stars, enterprise interest

---

*Created: 2026-01-29*
