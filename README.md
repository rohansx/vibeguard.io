# 🛡️ Vibeguard

**Know what your AI is doing. Always.**

Vibeguard is an open-source intent verification and audit system for AI agents. It logs every action, classifies risk, and lets you approve or block before things happen.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## The Problem

AI agents like Clawdbot, Claude Code, and GPT are getting root access to our lives — sending emails, deleting files, posting tweets, making purchases.

The only safeguard? "Are you sure? y/n"

**That's not good enough.**

## The Solution

Vibeguard sits between your AI agent and the actions it takes:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  AI Agent   │ ──▶ │  Vibeguard  │ ──▶ │   Action    │
│  (Claude)   │     │  (Approve?) │     │  (Execute)  │
└─────────────┘     └─────────────┘     └─────────────┘
```

**It provides:**
- 📝 **Action Logging** — See everything your agent does
- 🚦 **Risk Classification** — Automatic low/medium/high/critical ratings
- 🚪 **Intent Gating** — Approve or block before risky actions execute
- ↩️ **Undo** — One-click rollback for reversible actions
- 📊 **Dashboard** — Web UI to monitor and control

## Quick Start

```bash
# Install
npm install @vibeguard/sdk

# Use in your agent
import { vibeguard } from '@vibeguard/sdk';

// Wrap your action
const result = await vibeguard.guard({
  type: 'email.send',
  description: 'Send email to john@example.com',
  execute: () => sendEmail({ to, subject, body }),
});
```

## Example: Clawdbot Integration

```bash
# Coming soon: one-command install
npx vibeguard init --agent clawdbot
```

## Features

| Feature | Status |
|---------|--------|
| Action capture SDK | 🚧 In Progress |
| Risk classification | 🚧 In Progress |
| SQLite storage | 🚧 In Progress |
| CLI viewer | 📋 Planned |
| Intent gating | 📋 Planned |
| Web dashboard | 📋 Planned |
| Undo system | 📋 Planned |

## Why Open Source?

Trust requires transparency. If a tool is going to decide what your AI can do, you should be able to see exactly how it works.

## Documentation

- [Architecture](./docs/ARCHITECTURE.md)
- [Features](./docs/FEATURES.md)
- [Roadmap](./docs/ROADMAP.md)
- [Contributing](./CONTRIBUTING.md)

## Project Structure

```
vibeguard/
├── packages/
│   ├── core/        # Logging engine
│   ├── sdk/         # Agent integration
│   └── dashboard/   # Web UI
├── examples/
│   └── clawdbot/    # Example integration
└── docs/            # Documentation
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

MIT © 2026

---

**Website:** [vibeguard.io](https://vibeguard.io)
