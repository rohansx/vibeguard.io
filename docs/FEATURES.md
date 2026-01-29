# Vibeguard — Features

## Core Features

### 1. Action Logging

Every action your AI agent takes is captured and stored.

**What's logged:**
- What action was taken
- When it happened
- Which agent did it
- Why it thought it should (context)
- What the result was
- Risk level classification

**Example log entry:**
```
[2026-01-29 10:15:23] clawdbot
ACTION: Send email
TO: john@example.com
SUBJECT: Project Update
RISK: critical
CONTEXT: User asked to "send John the weekly update"
STATUS: approved → executed
```

### 2. Risk Classification

Automatic categorization of actions by risk level.

| Level | Examples | Default Behavior |
|-------|----------|------------------|
| 🟢 LOW | Read files, GET requests | Auto-approve, log |
| 🟡 MEDIUM | Write files, config changes | Log, notify |
| 🟠 HIGH | Delete files, shell commands | Require approval |
| 🔴 CRITICAL | Send email, social posts, payments | Always require approval |

**Customizable:** Users can adjust thresholds and add custom rules.

### 3. Intent Gating

Before risky actions execute, Vibeguard asks for confirmation.

```
┌─────────────────────────────────────────────────┐
│ 🛡️ VIBEGUARD - Approval Required               │
├─────────────────────────────────────────────────┤
│                                                 │
│ Your agent wants to:                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ Send an email to sarah@company.com              │
│ Subject: "Contract Proposal"                    │
│                                                 │
│ Risk Level: 🔴 CRITICAL                         │
│                                                 │
│ Context:                                        │
│ You said: "Draft a contract proposal for Sarah" │
│ Agent interpreted: Send email with proposal     │
│                                                 │
│ [✓ Approve]  [✗ Block]  [📋 View Full Content] │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 4. Undo Actions

One-click rollback for reversible actions.

**Supported undo operations:**
- ✅ File writes (restore from backup)
- ✅ File deletes (restore from trash)
- ✅ Config changes (restore previous)
- ✅ Git commits (revert)
- ⚠️ Emails (recall if supported)
- ⚠️ Social posts (delete)
- ❌ Payments (cannot undo)

### 5. Plain English Explanations

Every action comes with a human-readable explanation.

**Instead of:**
```json
{"tool":"exec","args":{"command":"rm -rf ./build/*"}}
```

**You see:**
```
Deleted all files in the 'build' folder to clean up
old compiled code before rebuilding the project.
```

### 6. Dashboard

Web-based UI to view and manage agent activity.

**Views:**
- **Timeline**: Chronological feed of all actions
- **By Agent**: Filter by specific AI agent
- **Alerts**: Actions that need attention
- **Settings**: Configure risk thresholds

**Actions:**
- Search and filter logs
- Undo reversible actions
- Export logs (JSON, CSV)
- Set up notifications

### 7. Notifications

Get alerted when agents do important things.

**Channels:**
- Desktop notifications
- Terminal alerts
- Telegram/Discord (optional)
- Email digest (optional)

**Configurable triggers:**
- All critical actions
- Blocked actions
- Failed actions
- Custom patterns

## Advanced Features

### 8. Policy Rules

Define custom rules for your agents.

```yaml
# vibeguard.yaml
rules:
  - name: "No emails after hours"
    condition:
      type: email.send
      time: "after 6pm"
    action: block
    
  - name: "Require approval for large files"
    condition:
      type: file.write
      size: "> 10MB"
    action: gate
    
  - name: "Always allow reading docs"
    condition:
      type: file.read
      path: "/docs/**"
    action: allow
```

### 9. Session Context

Group actions by conversation/session for better understanding.

```
Session: "Help me prepare the quarterly report"
├── Read file: sales_q4.csv
├── Read file: expenses_q4.csv
├── Create file: quarterly_report.md
├── [GATED] Send email: team@company.com
└── Session complete (4 actions, 1 gated)
```

### 10. Multi-Agent Support

Track multiple agents in one dashboard.

```
┌─────────────────────────────────────────────────┐
│ Agents                         Last Activity    │
├─────────────────────────────────────────────────┤
│ 🦞 clawdbot                    2 minutes ago   │
│ 🤖 claude-code                 1 hour ago      │
│ 📱 phone-agent                 3 hours ago     │
└─────────────────────────────────────────────────┘
```

### 11. Compliance Export

Export logs in compliance-friendly formats.

**Formats:**
- JSON (raw)
- CSV (spreadsheet)
- PDF (audit report)
- SIEM integration (Splunk, ELK)

**Includes:**
- Timestamp with timezone
- Agent identity
- Action details
- Approval chain
- Outcome

### 12. Local-First Privacy

Your data stays on your machine.

- SQLite database on disk
- No cloud required
- No telemetry
- Optional: sync to your own cloud
- Optional: team sharing

---

## Feature Roadmap Priority

### Phase 1 (MVP)
- [x] Action capture SDK
- [x] Risk classification
- [x] SQLite storage
- [ ] CLI viewer
- [ ] Basic intent gating

### Phase 2
- [ ] Web dashboard
- [ ] Undo system
- [ ] Clawdbot integration
- [ ] Desktop notifications

### Phase 3
- [ ] Policy rules engine
- [ ] Multi-agent support
- [ ] Team sharing
- [ ] Compliance exports

---

*Last updated: 2026-01-29*
