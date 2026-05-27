---
name: triage
description: Issue triage skill. Classifies incoming issues as bug, feature or question, maps priority (P0 to P3), flags missing checklist info, and generates response template.
---

# Issue Triage Skill

## Step 1: Classify
- "bug", "broken", "error", "crash", "fail", "not working" → Bug
- "add", "support", "would be great", "feature", "request" → Feature Request
- "how do I", "what is", "?" → Question

## Step 2: Priority
P0 signals: "production", "down", "all users", "data loss", "breach"
P1 signals: "blocks", "can't use", "critical", "urgent", no workaround
P2 signals: "sometimes", "occasionally", workaround exists
P3 signals: "minor", "nice to have", "cosmetic"

## Step 3: Completeness Checklist
A complete bug report has:
- What they tried to do
- What happened (error, screenshot)
- What they expected
- How to reproduce
- Their environment (OS, version)

## Step 4: Labels
Bug + P0/P1 → ["bug", "P1", "needs-investigation"]
Bug + P2/P3 → ["bug", "P2"]
Feature → ["enhancement"]
Question → ["question"]
Missing info → ["needs-more-info"]
