# VibeGuard

**AI Code Compliance Platform**

> "Compliance for AI-generated code"

## The Problem

- **42%** of code is now AI-generated (Sonar 2026)
- **96%** of devs don't fully trust it
- **48%** actually verify before committing
- **0%** have audit trails for AI code

Enterprise has zero visibility into what AI is writing. Regulators are starting to notice.

## The Solution

VibeGuard is a compliance layer that:

1. **Detects** AI-generated code in commits, PRs, and codebases
2. **Enforces** review policies (block, require approval, route to security)
3. **Audits** with compliance-ready documentation for SOC 2, EU AI Act, ISO 27001

## Quick Start

```bash
# Install CLI
npm install -g @vibeguard/cli

# Scan a PR
vibeguard scan --pr 1234

# Run in CI
vibeguard ci --policy strict
```

## Features

### Detection
- ML-powered AI code detection
- Per-file confidence scores
- Historical codebase analysis
- IDE integration (VS Code, JetBrains)

### Enforcement
- Custom policy rules
- CI/CD gates
- Required reviewers for AI code
- Risk-based routing

### Audit
- Audit trail exports
- SOC 2 evidence packs
- Trend dashboards
- API for integrations

## Compliance Coverage

| Framework | Coverage |
|-----------|----------|
| EU AI Act | AI system documentation |
| SOC 2 Type II | AI governance evidence |
| ISO 27001 | AI risk controls |
| SEC Cybersecurity | Breach disclosure readiness |

## Why "VibeGuard"?

"Vibe coding" = writing software with AI assistance without fully understanding what's generated.

It's fast. It's also risky:
- Security vulnerabilities from hallucinations
- License/IP issues from training data
- Compliance gaps with no audit trail
- Technical debt from code nobody comprehends

**VibeGuard** = protection against the risks of vibe coding.

## Links

- Website: https://vibeguard.io
- Docs: https://docs.vibeguard.io
- API: https://api.vibeguard.io

## License

Proprietary - All rights reserved
