# Secret Detection Patterns

## Critical — Flag Immediately
- sk-ant-[a-zA-Z0-9]+ — Anthropic API key
- sk-[a-zA-Z0-9]{48} — OpenAI API key
- ghp_[a-zA-Z0-9]{36} — GitHub token
- AKIA[0-9A-Z]{16} — AWS Access Key
- password = "anything_here" — Hardcoded password
- secret = "anything_here" — Hardcoded secret
- api_key = "anything_here" — Hardcoded API key
- -----BEGIN RSA PRIVATE KEY----- — Private key

## Medium — Investigate
- Connection strings with passwords embedded
- JWT secrets hardcoded in source
- Database URLs with credentials
