# Vibeguard — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI Agent                                 │
│  (Clawdbot, Claude Code, GPT Operator, Custom Agents)           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Vibeguard SDK                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Capture   │  │  Classify   │  │      Gate (Intent)      │ │
│  │   Actions   │──│   Risk      │──│   Approve / Block       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Vibeguard Core                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Action Log │  │  Undo       │  │      Explain            │ │
│  │  (SQLite)   │  │  Registry   │  │   (Plain English)       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Vibeguard Dashboard                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Timeline   │  │  Alerts     │  │      Settings           │ │
│  │  View       │  │  & Notifs   │  │   (Risk Levels, etc.)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Vibeguard SDK (`@vibeguard/sdk`)

Lightweight library that AI agents integrate with.

**Responsibilities:**
- Intercept actions before execution
- Classify action risk level
- Apply intent gates (approval flows)
- Send action data to core

**Key APIs:**
```typescript
vibeguard.capture(action: Action): Promise<void>
vibeguard.gate(action: Action, level: RiskLevel): Promise<boolean>
vibeguard.undo(actionId: string): Promise<UndoResult>
```

### 2. Vibeguard Core (`@vibeguard/core`)

Local-first engine that stores and processes action data.

**Responsibilities:**
- Persist action logs (SQLite by default)
- Maintain undo registry (reversible actions)
- Generate plain-English explanations
- Expose query APIs

**Storage:**
- SQLite for local persistence
- Optional: PostgreSQL for teams
- Optional: Export to cloud (user opt-in)

### 3. Vibeguard Dashboard (`@vibeguard/dashboard`)

Web UI for humans to see what their agents did.

**Features:**
- Timeline view of all actions
- Filter by risk level, agent, time
- One-click undo for reversible actions
- Alert configuration
- Export logs (JSON, CSV)

## Data Model

### Action

```typescript
interface Action {
  id: string;                    // UUID
  timestamp: Date;               // When it happened
  agent: string;                 // Which agent (clawdbot, claude, etc.)
  type: ActionType;              // Category of action
  description: string;           // Human-readable description
  details: Record<string, any>;  // Raw action data
  risk: RiskLevel;               // low | medium | high | critical
  status: ActionStatus;          // pending | approved | executed | blocked | undone
  context: ActionContext;        // Why the agent did this
  reversible: boolean;           // Can it be undone?
  undoFn?: string;               // Serialized undo function
}
```

### ActionType (Categories)

```typescript
enum ActionType {
  // File System
  FILE_READ = 'file.read',
  FILE_WRITE = 'file.write',
  FILE_DELETE = 'file.delete',
  
  // Network
  HTTP_REQUEST = 'http.request',
  EMAIL_SEND = 'email.send',
  MESSAGE_SEND = 'message.send',
  
  // Code Execution
  SHELL_COMMAND = 'shell.command',
  CODE_EXECUTE = 'code.execute',
  
  // External Services
  API_CALL = 'api.call',
  PAYMENT = 'payment',
  SOCIAL_POST = 'social.post',
  
  // System
  CONFIG_CHANGE = 'config.change',
  PERMISSION_CHANGE = 'permission.change',
}
```

### RiskLevel

```typescript
enum RiskLevel {
  LOW = 'low',           // Read-only, reversible
  MEDIUM = 'medium',     // Write, but reversible
  HIGH = 'high',         // External side-effects
  CRITICAL = 'critical', // Irreversible, sensitive
}
```

## Risk Classification Rules

| Action | Default Risk | Reason |
|--------|--------------|--------|
| Read file | LOW | No side effects |
| Write file | MEDIUM | Reversible if backup exists |
| Delete file | HIGH | Data loss potential |
| Send email | CRITICAL | Irreversible, external |
| Post to social | CRITICAL | Public, reputational |
| Shell command | HIGH | Could be anything |
| HTTP GET | LOW | Read-only |
| HTTP POST/PUT | MEDIUM-HIGH | Depends on endpoint |
| Payment | CRITICAL | Financial |

## Intent Gating

When an action exceeds the user's configured threshold, Vibeguard gates it:

```
[VIBEGUARD] Action requires approval
────────────────────────────────────
Agent: clawdbot
Action: Send email to john@example.com
Risk Level: CRITICAL
Reason: External communication, irreversible

Context: User asked to "follow up with John about the project"

[A]pprove  [B]lock  [M]ore info
```

## Undo System

For reversible actions, Vibeguard stores undo functions:

```typescript
interface UndoRegistry {
  actionId: string;
  undoFn: () => Promise<void>;  // Serialized function
  expiresAt: Date;              // How long undo is available
  state: 'available' | 'executed' | 'expired';
}
```

**Undo strategies by action type:**
- File write: Restore from backup
- File delete: Restore from trash
- Config change: Restore previous config
- Email: Mark as "recalled" (limited)
- Social post: Delete post

## Tech Stack

| Component | Technology |
|-----------|------------|
| SDK | TypeScript, zero dependencies |
| Core | Node.js, SQLite (better-sqlite3) |
| Dashboard | React, Tailwind, Vite |
| CLI | Node.js, Commander |
| Monorepo | Turborepo, pnpm |

## Integration Points

### Clawdbot Integration

```typescript
// In Clawdbot's tool execution
import { vibeguard } from '@vibeguard/sdk';

async function executeToolCall(tool, args) {
  const action = vibeguard.capture({
    type: mapToolToActionType(tool),
    description: `Execute ${tool.name}`,
    details: { tool, args },
    context: getCurrentContext(),
  });
  
  const approved = await vibeguard.gate(action);
  if (!approved) {
    return { blocked: true, reason: 'User declined' };
  }
  
  const result = await tool.execute(args);
  
  vibeguard.complete(action.id, { result });
  return result;
}
```

### Generic Agent Integration

```typescript
import { createVibeguard } from '@vibeguard/sdk';

const guard = createVibeguard({
  agent: 'my-agent',
  riskThreshold: 'medium',  // Gate everything medium+
  storage: 'local',         // or 'postgres://...'
});

// Wrap any function
const safeSendEmail = guard.wrap(sendEmail, {
  type: 'email.send',
  risk: 'critical',
});

await safeSendEmail({ to, subject, body });
```

## Security Considerations

1. **Local-first**: Logs stored locally by default
2. **No telemetry**: Zero data sent anywhere without opt-in
3. **Encryption at rest**: Optional SQLite encryption
4. **Audit immutability**: Append-only log mode available
5. **Credential redaction**: Auto-redact secrets from logs

---

*Last updated: 2026-01-29*
