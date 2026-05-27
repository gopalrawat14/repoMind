---
name: vuln-scan
description: Autonomous vulnerability scanner. Checks diffs for credentials, injection, path traversal, SSRF and other security bugs.
---

# Vulnerability Scanning Skill

## Input
A git diff in patch format.

## Steps
1. Parse every added line (lines starting with +)
2. Check against secret-patterns.md
3. Check against owasp-top10.md
4. Perform semantic analysis for injection patterns
5. Ignore lines starting with ++ (diff headers) or +++ (file headers)

## False Positive Reduction
- Ignore comments that describe vulnerabilities (not actual code)
- Ignore test files with obviously fake values: test_, dummy_, fake_, example_
- localhost and 127.0.0.1 are LOW not HIGH
- example.com URLs are not SSRF risks

## Output
Structured findings with: severity, file, line, issue, fix
