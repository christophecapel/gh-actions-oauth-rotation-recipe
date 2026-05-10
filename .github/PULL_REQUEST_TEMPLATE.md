<!-- Thanks for the PR. Please fill in the sections below. -->

## Summary

<!-- One or two sentences describing the change. -->

## Why

<!-- Link the issue this addresses, or describe the problem if no issue exists. -->

## Type of change

- [ ] Bug fix (existing behavior was wrong)
- [ ] Adoption-guide update (new provider-specific gotcha)
- [ ] Test addition (new regression coverage)
- [ ] Documentation (README, failure-modes, security)
- [ ] Other (explain below)

## Test plan

- [ ] `python3 -m unittest tests.test_refresh -v` — all green
- [ ] CI green on this branch
- [ ] If the workflow yaml changed: validated with `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/rotation.yml'))"`
- [ ] CHANGELOG.md entry added under `## [Unreleased]`

## Scope check

- [ ] This change keeps the recipe provider-agnostic (or documents the provider-specific path explicitly in `docs/adoption.md`)
- [ ] No new dependencies added (or, if added, justified in the PR body)
- [ ] No em dashes in markdown changes (repo convention)
