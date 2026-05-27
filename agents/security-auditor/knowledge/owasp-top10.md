# OWASP Top 10 Quick Reference

## A01 Broken Access Control
- Missing auth checks before data access
- Direct object references without ownership check

## A02 Cryptographic Failures
- md5( or sha1( for passwords
- Hardcoded encryption keys
- HTTP instead of HTTPS for sensitive data

## A03 Injection
- SQL: f"SELECT * FROM users WHERE id={user_input}"
- Command: os.system(user_input), subprocess with shell=True
- Pattern: execute(f", os.system(, shell=True

## A05 Security Misconfiguration
- DEBUG=True in production
- Default credentials
- Overly permissive CORS: "*"

## A08 Software Integrity Failures
- pickle.loads(user_data)
- yaml.load() instead of yaml.safe_load()

## A09 Logging Failures
- Passwords or tokens in log statements
- Pattern: logger.info(.*password, print(.*token
