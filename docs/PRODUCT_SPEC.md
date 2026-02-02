# VibeGuard: AI Code Compliance Platform

**Domain:** vibeguard.io

## Executive Summary

**One-liner:** "Compliance for AI-generated code"

**The Problem:**
- 42% of code is now AI-generated (Sonar 2026)
- 96% of developers don't trust it, but only 48% verify it
- Enterprises have zero visibility into what AI is writing
- EU AI Act, SOC 2, and SEC rules increasingly require AI audit trails

**The Solution:**
A compliance layer that detects AI-generated code, enforces review policies, and provides audit-ready documentation.

**Target Buyer:** CISO, VP of Engineering, Compliance teams at companies with 50+ engineers

---

## Priority Matrix

| Feature | Priority | Rationale |
|---------|----------|-----------|
| Pre-commit gates | **P0** | Unique differentiator, immediate value |
| AI code detection | **P0** | Core capability |
| License/provenance detection | **P1** | JFrog doing this — need parity |
| AI-specific vuln scanning | **P1** | Hallucinations, prompt injection, hardcoded secrets |
| Policy engine | **P1** | Enterprise requirement |
| Audit trail export | **P1** | Compliance selling point |
| Review tracking | **P2** | Nice-to-have |
| Dashboard | **P2** | Needed for enterprise |
| Comprehension metrics | **P3** | Future differentiator |

---

## Detection Methods

| Method | Accuracy | How It Works |
|--------|----------|--------------|
| **IDE Telemetry** | 99% | Direct capture from Copilot/Cursor extensions |
| **Stylometry** | 75-85% | Writing patterns, naming conventions, consistency |
| **Pattern Matching** | 80-90% | Known AI code signatures and boilerplate |
| **ML Classifier** | 70-80% | Trained model on AI vs human code |
| **Timing Heuristics** | 60-70% | Commit velocity anomalies |

---

## 90-Day Execution Plan

### Month 1: Foundation
- [ ] Monorepo setup (Go + Python + React)
- [ ] PostgreSQL + TimescaleDB schema
- [ ] Basic API skeleton
- [ ] GitHub App registration
- [ ] Webhook handler for PR events
- [ ] Stylometry analysis (Python)
- [ ] Pattern matching rules
- [ ] Basic confidence scoring

### Month 2: Core Product
- [ ] YAML policy parser
- [ ] Rule evaluation engine
- [ ] GitHub status checks integration
- [ ] Block/warn/require-review actions
- [ ] Secret detection
- [ ] Basic injection pattern scanning
- [ ] Audit trail logging

### Month 3: Launch
- [ ] Dashboard MVP (React)
- [ ] VS Code extension (telemetry)
- [ ] Documentation
- [ ] 5 design partner onboarding
- [ ] Product Hunt prep

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| API Gateway | Kong / AWS API Gateway |
| API Services | Go |
| Detection Engine | Python |
| Policy Engine | Go |
| Security Scanner | Go + Semgrep |
| Dashboard | React + TypeScript + Tailwind |
| Database | PostgreSQL + TimescaleDB |
| Queue | Redis Streams |
| Storage | S3 |

---

## Pricing

| Tier | Price | Target |
|------|-------|--------|
| Starter | Free | Solo devs, evaluation |
| Team | $29/seat/mo | Growing teams (10-50) |
| Enterprise | $59/seat/mo | Large orgs (50+) |
| On-Prem | Custom | Regulated industries |

---

## Success Metrics

| Metric | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|----------|
| Repos Connected | 25 | 250 | 2,500 |
| Commits Analyzed | 5K | 250K | 5M |
| Paying Customers | 5 | 30 | 150 |
| MRR | $2K | $20K | $120K |
