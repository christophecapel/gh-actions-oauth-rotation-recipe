# Security Policy

## Reporting a Vulnerability

This repo contains executable Python and a workflow yaml pattern. Genuine security issues in the rotation logic, the secret-encryption path, or the example workflow are taken seriously.

**How to report:**

- **Preferred**: GitHub's [private vulnerability reporting](https://github.com/christophecapel/gh-actions-oauth-rotation-recipe/security/advisories/new)
- **Alternative**: DM [@christophecapel](https://github.com/christophecapel) on GitHub

**Please do not open public issues for security reports.** Public issues are appropriate for bug reports, feature requests, and adoption-guide gotchas: but not vulnerabilities.

## What counts as a security issue

- A bug in `scripts/refresh_token.py` or `scripts/update_secret.py` that could leak credentials (e.g., logging the secret value, persisting it to an unexpected location, sending it to an unintended endpoint)
- A workflow yaml pattern that could expose secrets via run logs (e.g., printing `$GH_PAT` to stdout)
- A dependency chain (`requests`, `pynacl`) compromise that affects this recipe specifically
- A supply-chain concern with the recipe's distribution (typosquatting, malicious fork)

## What is NOT a security issue

- Adopters who set GH_PAT with broader scope than needed (covered in `docs/adoption.md`)
- Adopters who commit `.tokens.json` instead of `.gitignore`-ing it (the file is intended to be committed in the example workflow; that's the whole point: the gitignore in this repo is for local-dev safety only)
- General OAuth provider security questions (those belong with the provider, not here)

## Response timeline

- **Acknowledgment**: within 7 days
- **Initial assessment**: within 14 days
- **Fix**: aimed for 30 days from acknowledgment for critical issues, 90 days for non-critical

## Disclosure

After a fix lands, the vulnerability is disclosed via a GitHub Security Advisory and a `CHANGELOG.md` note. Reporters are credited (with permission).

No bug bounty program: this is a personal-scale recipe. Reports are appreciated regardless.
