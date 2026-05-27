---
name: routing
description: Given a GitHub webhook payload, decide which agents to invoke.
---

# Event Routing Skill

Given a GitHub webhook payload, decide which agents to invoke.

Routing matrix:
- PR with auth/secret/password/key in title or files -> security-auditor (CRITICAL)
- PR with any code changes -> perf-reviewer
- PR with .md/.rst files only -> doc-writer
- Issue opened -> bug-triager
- Push to main -> security-auditor

Always return valid JSON. No explanation, just JSON.
