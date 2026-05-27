---
name: docgen
description: Documentation generation skill. Parses git diffs for undocumented classes/functions and writes high-quality Google-style docstrings, README files, or CHANGELOG updates.
---

# Documentation Generation Skill

## Finding Undocumented Code
In the diff, look for:
- Lines starting with + def (new Python function)
- Lines starting with + class (new Python class)
- Lines starting with + export function (new JS/TS function)
- Lines starting with + export class (new JS/TS class)

## Checking Existing Docs
After a def line, check if the next line (after +) starts with """.
If not — it needs a docstring.

## Writing Good Docstrings
- First line: what it does (verb phrase, imperative mood)
- Args: each parameter, its type, what it means
- Returns: what comes back
- Example: a real working usage example
- Raises: what exceptions can be thrown

## CHANGELOG Format
## [Unreleased]
### Added
- New feature description
### Changed
- Changed behavior description
### Fixed
- Bug fix description
